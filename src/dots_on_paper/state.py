"""Durable state and idempotent reply events. No network or device credentials."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

CHARACTERS = ("artist", "curious", "bookish", "cool")
STATUSES = ("idle", "thinking", "answer", "error")
FIELDS = {"status", "character", "dot_name", "title", "text", "event_id", "run_id"}
ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


class StateError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_event(event: object) -> dict:
    if not isinstance(event, dict):
        raise StateError("Event must be a JSON object")
    if set(event) - FIELDS:
        raise StateError("Event has unknown fields")
    if event.get("status") not in STATUSES:
        raise StateError("status must be idle, thinking, answer or error")
    if "character" in event and event["character"] not in CHARACTERS:
        raise StateError("Unknown character")
    result = dict(event)
    for key, maximum in (("dot_name", 80), ("title", 120), ("text", 12000)):
        if key in result:
            value = result[key]
            if not isinstance(value, str) or len(value) > maximum:
                raise StateError(f"{key} must be a string of at most {maximum} characters")
            if any(ord(char) < 32 and char not in "\n\t" for char in value):
                raise StateError(f"{key} contains unsupported control characters")
            if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
                raise StateError(f"{key} contains invalid Unicode")
    if result["status"] == "answer" and not result.get("text", "").strip():
        raise StateError("An answer requires nonempty text")
    for key in ("event_id", "run_id"):
        if key in result and (not isinstance(result[key], str) or not ID_PATTERN.fullmatch(result[key])):
            raise StateError(f"{key} must contain 1–128 letters, numbers, underscores, dots, colons or hyphens")
    return result


class StateStore:
    def __init__(self, path: str | Path):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK (id = 1), value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, digest TEXT NOT NULL, revision INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, status TEXT NOT NULL, revision INTEGER NOT NULL);
        """)
        initial = dict(status="idle", character="artist", dot_name="Your dot", title="DOTS ON PAPER",
                       text="", revision=0, event_id="", run_id="", updated_at=now())
        self.db.execute("INSERT OR IGNORE INTO state VALUES (1, ?)", (json.dumps(initial),))
        self.db.commit()

    def read(self) -> dict:
        with self.lock:
            return json.loads(self.db.execute("SELECT value FROM state WHERE id = 1").fetchone()[0])

    def _write(self, state: dict):
        self.db.execute("UPDATE state SET value = ? WHERE id = 1", (json.dumps(state, ensure_ascii=False),))

    def apply(self, value: object) -> dict:
        event = validate_event(value)
        digest = hashlib.sha256(json.dumps(event, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        event_id = event.get("event_id") or str(uuid.uuid4())
        with self.lock, self.db:
            prior = self.db.execute("SELECT digest FROM events WHERE event_id = ?", (event_id,)).fetchone()
            if prior:
                if prior[0] != digest:
                    raise StateError("event_id was already used with different content", 409)
                return self.read()
            current = self.read()
            status = event["status"]
            run_id = event.get("run_id") or str(uuid.uuid4())
            prior_run = self.db.execute("SELECT status FROM runs WHERE run_id = ?", (run_id,)).fetchone()
            if prior_run and prior_run[0] != "thinking":
                raise StateError("This run is already completed or superseded", 409)
            if status != "thinking" and event.get("run_id") and (current["status"] != "thinking" or current["run_id"] != run_id):
                raise StateError("Explicit completion requires the current active thinking run", 409)
            if current["status"] == "thinking" and current["run_id"] != run_id:
                self.db.execute("UPDATE runs SET status = 'superseded' WHERE run_id = ?", (current["run_id"],))
            current.update({key: event[key] for key in ("character", "dot_name", "title") if key in event})
            current.update(status=status, text=event.get("text", ""), event_id=event_id, run_id=run_id,
                           revision=current["revision"] + 1, updated_at=now())
            self._write(current)
            self.db.execute("INSERT INTO events VALUES (?, ?, ?)", (event_id, digest, current["revision"]))
            self.db.execute("INSERT OR REPLACE INTO runs VALUES (?, ?, ?)", (run_id, status, current["revision"]))
            # Keep bounded retry/run history; display state survives independently.
            cutoff = current["revision"] - 1000
            self.db.execute("DELETE FROM events WHERE revision < ?", (cutoff,))
            self.db.execute("DELETE FROM runs WHERE revision < ? AND status != 'thinking'", (cutoff,))
            return current

    def select(self, value: object) -> dict:
        if not isinstance(value, dict) or set(value) != {"character"} or value["character"] not in CHARACTERS:
            raise StateError("Settings require only a valid character")
        with self.lock, self.db:
            current = self.read()
            if current["character"] != value["character"]:
                current.update(character=value["character"], revision=current["revision"] + 1, updated_at=now())
                self._write(current)
            return current

    def close(self):
        with self.lock:
            self.db.close()
