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
DISPLAY_MODES = ("last_reply", "full_conversation")
MAX_MESSAGES = 20
MAX_CONVERSATION_CHARS = 24000
FIELDS = {"status", "character", "dot_name", "title", "text", "event_id", "run_id", "mode", "user_text", "messages"}
ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


class StateError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_text(value: object, key: str, maximum: int, *, nonempty: bool = False) -> str:
    if not isinstance(value, str) or len(value) > maximum:
        raise StateError(f"{key} must be a string of at most {maximum} characters")
    if nonempty and not value.strip():
        raise StateError(f"{key} requires nonempty text")
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise StateError(f"{key} contains unsupported control characters")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise StateError(f"{key} contains invalid Unicode")
    return value


def validate_messages(value: object) -> list[dict]:
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_MESSAGES:
        raise StateError(f"messages must contain 1–{MAX_MESSAGES} user or assistant turns")
    messages = []
    for message in value:
        if not isinstance(message, dict) or set(message) - {"role", "content", "meta"} or message.get("role") not in ("user", "assistant"):
            raise StateError("Each message requires user or assistant role, content and optional meta")
        content = validate_text(message.get("content"), "message content", 12000, nonempty=True)
        turn = dict(role=message["role"], content=content)
        if "meta" in message:
            turn["meta"] = validate_text(message["meta"], "message meta", 120)
        messages.append(turn)
    if sum(len(message["content"]) for message in messages) > MAX_CONVERSATION_CHARS:
        raise StateError(f"Conversation content must be at most {MAX_CONVERSATION_CHARS} characters")
    return messages


def bound_messages(messages: list[dict]) -> list[dict]:
    messages = list(messages[-MAX_MESSAGES:])
    while sum(len(message["content"]) for message in messages) > MAX_CONVERSATION_CHARS:
        messages.pop(0)
    return messages


def validate_event(event: object) -> dict:
    if not isinstance(event, dict):
        raise StateError("Event must be a JSON object")
    if set(event) - FIELDS:
        raise StateError("Event has unknown fields")
    if event.get("status") not in STATUSES:
        raise StateError("status must be idle, thinking, answer or error")
    if "character" in event and event["character"] not in CHARACTERS:
        raise StateError("Unknown character")
    if "mode" in event and event["mode"] not in DISPLAY_MODES:
        raise StateError("mode must be last_reply or full_conversation")
    result = dict(event)
    for key, maximum in (("dot_name", 80), ("title", 120), ("text", 12000)):
        if key in result:
            validate_text(result[key], key, maximum)
    if result["status"] == "answer" and not result.get("text", "").strip():
        raise StateError("An answer requires nonempty text")
    if "user_text" in result:
        validate_text(result["user_text"], "user_text", 12000, nonempty=True)
        if result["status"] not in ("thinking", "answer"):
            raise StateError("user_text is supported only for thinking or answer")
    if "messages" in result:
        if result["status"] != "answer" or "user_text" in result:
            raise StateError("messages is supported only for answer and cannot be combined with user_text")
        result["messages"] = validate_messages(result["messages"])
        latest = result["messages"][-1]
        if latest["role"] != "assistant" or latest["content"] != result["text"]:
            raise StateError("messages must end with the assistant reply supplied in text")
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
                       text="", mode="last_reply", messages=[], revision=0, event_id="", run_id="", updated_at=now())
        self.db.execute("INSERT OR IGNORE INTO state VALUES (1, ?)", (json.dumps(initial),))
        # Upgrade an existing bridge without discarding its retained answer.
        current = json.loads(self.db.execute("SELECT value FROM state WHERE id = 1").fetchone()[0])
        if "mode" not in current or "messages" not in current:
            current.setdefault("mode", "last_reply")
            current.setdefault("messages", [dict(role="assistant", content=current["text"])]
                               if current.get("status") == "answer" and current.get("text", "").strip() else [])
            self._write(current)
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
            messages = event.get("messages", list(current["messages"]))
            if "user_text" in event:
                user = dict(role="user", content=event["user_text"])
                # A thinking event can establish the prompt before completion.
                # Repeating it for the same run must not add duplicate turns.
                same_run = current["run_id"] == run_id and current["status"] == "thinking"
                if not (same_run and messages and messages[-1] == user):
                    messages.append(user)
            if status == "answer" and "messages" not in event:
                messages.append(dict(role="assistant", content=event["text"]))
            current.update({key: event[key] for key in ("character", "dot_name", "title", "mode") if key in event})
            current.update(status=status, text=event.get("text", ""), event_id=event_id, run_id=run_id,
                           messages=bound_messages(messages), revision=current["revision"] + 1, updated_at=now())
            self._write(current)
            self.db.execute("INSERT INTO events VALUES (?, ?, ?)", (event_id, digest, current["revision"]))
            self.db.execute("INSERT OR REPLACE INTO runs VALUES (?, ?, ?)", (run_id, status, current["revision"]))
            # Keep bounded retry/run history; display state survives independently.
            cutoff = current["revision"] - 1000
            self.db.execute("DELETE FROM events WHERE revision < ?", (cutoff,))
            self.db.execute("DELETE FROM runs WHERE revision < ? AND status != 'thinking'", (cutoff,))
            return current

    def select(self, value: object) -> dict:
        if not isinstance(value, dict) or not value or set(value) - {"character", "mode"}:
            raise StateError("Settings require character and/or mode")
        if "character" in value and value["character"] not in CHARACTERS:
            raise StateError("Unknown character")
        if "mode" in value and value["mode"] not in DISPLAY_MODES:
            raise StateError("mode must be last_reply or full_conversation")
        with self.lock, self.db:
            current = self.read()
            if any(current[key] != setting for key, setting in value.items()):
                current.update(value, revision=current["revision"] + 1, updated_at=now())
                self._write(current)
            return current

    def close(self):
        with self.lock:
            self.db.close()
