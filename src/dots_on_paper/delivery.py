"""Durable, coalesced finished-card uploads. A receipt is not panel observation."""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .config import PROFILES
from .render import render_image

MAX_IMAGE_BYTES = 1_000_000
UPLOAD_INTERVAL = 300


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        return None


def retry_seconds(value: str | None, clock: float) -> float:
    try:
        delay = float(value)
    except (TypeError, ValueError):
        try:
            delay = parsedate_to_datetime(value).timestamp() - clock
        except (TypeError, ValueError, OverflowError):
            delay = 300
    return min(86400, max(0, delay))


def upload(url: str, payload: bytes) -> tuple[int, str | None]:
    try:
        with build_opener(NoRedirect).open(Request(url, data=payload, headers={"Content-Type": "image/png"}, method="POST"), timeout=10) as response:
            return response.status, response.headers.get("Retry-After")
    except HTTPError as error:
        code, retry = error.code, error.headers.get("Retry-After")
        error.close()
        return code, retry
    except (URLError, TimeoutError, OSError):
        # Exception strings may contain the private webhook URL.
        return 0, None


class WebhookDelivery:
    def __init__(self, store, config, *, uploader=upload, clock=time.time):
        self.store, self.config, self.uploader, self.clock = store, config, uploader, clock
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run, name="dots-webhook", daemon=True)
        self.thread.start()

    def _run(self):
        while not self.stop_event.is_set():
            try:
                self.tick()
            except Exception:
                self.store.mark("delivery_status", json.dumps(dict(status="temporary_error", detail="Delivery will retry; no request data logged")))
            self.stop_event.wait(2)

    def close(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(12)

    def _pending(self):
        row = self.store.db.execute("SELECT value FROM delivery WHERE id = 1").fetchone()
        return json.loads(row[0]) if row else None

    def enqueue(self, state: dict):
        with self.lock, self.store.lock, self.store.db:
            seen = self.store.metadata().get("delivery_seen_revision")
            if seen == str(state["revision"]):
                return
            pending = dict(state={key: value for key, value in state.items() if key != "last_result"}, attempts=0, next_at=0, blocked=False)
            self.store.db.execute("INSERT OR REPLACE INTO delivery VALUES (1, ?)", (json.dumps(pending, ensure_ascii=False),))
            self.store.db.execute("INSERT OR REPLACE INTO metadata VALUES ('delivery_seen_revision', ?)", (str(state["revision"]),))

    def tick(self):
        with self.lock:
            state = self.store.read()
            metadata = self.store.metadata()
            # Recover a committed answer even if the process stopped before enqueue.
            if state["status"] == "answer" or metadata.get("delivery_clear_revision") == str(state["revision"]):
                self.enqueue(state)
            clock = self.clock()
            with self.store.lock, self.store.db:
                pending = self._pending()
                if not pending or pending["blocked"] or pending["next_at"] > clock:
                    return
                self.store.db.execute("DELETE FROM delivery_attempts WHERE timestamp <= ?", (clock - 3600,))
                attempts = [row[0] for row in self.store.db.execute("SELECT timestamp FROM delivery_attempts ORDER BY timestamp")]
                if attempts and clock < attempts[-1] + UPLOAD_INTERVAL:
                    return
                if len(attempts) >= 12:
                    return
            image_state = dict(pending["state"])
            image_state["display_budget"] = 1200 if self.config.webhook_profile == "trmnl_x" else 420
            payload = render_image(image_state, **PROFILES[self.config.webhook_profile], frame=11)
            if len(payload) > MAX_IMAGE_BYTES:
                code, retry = 422, None
            else:
                with self.store.lock, self.store.db:
                    self.store.db.execute("INSERT INTO delivery_attempts VALUES (?)", (clock,))
                code, retry = self.uploader(self.config.webhook_url, payload)
            accepted = 200 <= code < 300
            temporary = code in (0, 408, 425, 429) or code >= 500
            pending["attempts"] += 1
            pending["blocked"] = not accepted and not temporary
            pending["next_at"] = clock + max(UPLOAD_INTERVAL, retry_seconds(retry, clock) if code == 429 else min(3600, 60 * 2 ** min(pending["attempts"], 6)))
            receipt = dict(status="accepted" if accepted else "retrying" if temporary else "blocked",
                           http_status=code, revision=pending["state"]["revision"], image_bytes=len(payload),
                           checked_at=datetime.fromtimestamp(clock, timezone.utc).isoformat())
            with self.store.lock, self.store.db:
                current = self._pending()
                if current and current["state"]["revision"] == pending["state"]["revision"]:
                    if accepted:
                        self.store.db.execute("DELETE FROM delivery")
                    else:
                        self.store.db.execute("UPDATE delivery SET value = ? WHERE id = 1", (json.dumps(pending),))
                self.store.db.execute("INSERT OR REPLACE INTO metadata VALUES ('delivery_status', ?)", (json.dumps(receipt),))
                if accepted:
                    self.store.db.execute("INSERT OR REPLACE INTO metadata VALUES ('delivery_last_accepted', ?)", (json.dumps(receipt),))

    def retry(self):
        with self.lock, self.store.lock, self.store.db:
            pending = self._pending()
            if pending:
                pending.update(blocked=False, next_at=0)
                self.store.db.execute("UPDATE delivery SET value = ? WHERE id = 1", (json.dumps(pending),))

    def status(self):
        with self.store.lock:
            pending = self._pending()
            metadata = self.store.metadata()
            return dict(configured=True, profile=self.config.webhook_profile, cloud_dependent=True,
                        pending_revision=pending["state"]["revision"] if pending else None,
                        blocked=bool(pending and pending["blocked"]), next_attempt_at=pending["next_at"] if pending else None,
                        last_attempt=json.loads(metadata.get("delivery_status", "null")),
                        last_accepted=json.loads(metadata.get("delivery_last_accepted", "null")), panel_observed=False)
