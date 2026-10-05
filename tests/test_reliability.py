"""Interrupted tasks, deliberate clearing, pairing and durable delivery contracts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from dots_on_paper.config import Config
from dots_on_paper.delivery import MAX_IMAGE_BYTES, WebhookDelivery, upload
from dots_on_paper.render import render_image
from dots_on_paper.state import StateError, StateStore
from dots_on_paper.server import BridgeServer

API = "publish-test-" + "a" * 32
IMAGE = "image-test-" + "b" * 32


class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "state.sqlite3"
        self.store = StateStore(self.path, 60)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def expire(self):
        with self.store.lock, self.store.db:
            state = self.store.read()
            state["thinking_since"] = (datetime.now(timezone.utc) - timedelta(seconds=61)).isoformat()
            self.store._write(state)

    def test_timeout_keeps_completed_result_and_rejects_late_completion(self):
        answer = self.store.apply(dict(status="answer", text="Keep this report", source="Desk assistant"))
        self.store.apply(dict(status="thinking", run_id="interrupted", user_text="Next task"))
        self.expire()
        state = self.store.read()
        self.assertEqual((state["status"], state["title"]), ("error", "No recent update"))
        self.assertEqual(state["last_result"]["text"], answer["text"])
        self.assertEqual(self.store.read()["revision"], state["revision"])
        with self.assertRaises(StateError):
            self.store.apply(dict(status="answer", run_id="interrupted", text="Too late"))
        restored = self.store.restore()
        self.assertEqual((restored["text"], restored["updated_at"]), (answer["text"], answer["updated_at"]))
        self.assertEqual(restored["status"], "answer")

    def test_restart_expires_an_old_run_without_losing_prior_answer(self):
        self.store.apply(dict(status="answer", text="Last useful answer"))
        self.store.apply(dict(status="thinking", run_id="restart"))
        self.expire()
        self.store.close()
        self.store = StateStore(self.path, 60)
        state = self.store.read()
        self.assertEqual(state["recovery_reason"], "timeout")
        self.assertEqual(state["last_result"]["text"], "Last useful answer")

    def test_same_run_and_character_changes_do_not_extend_deadline_or_result_time(self):
        answer = self.store.apply(dict(status="answer", text="A report"))
        self.assertEqual(self.store.select(dict(character="cool"))["updated_at"], answer["updated_at"])
        first = self.store.apply(dict(status="thinking", run_id="same"))
        repeated = self.store.apply(dict(status="thinking", run_id="same", title="Still working"))
        self.assertEqual(first["thinking_since"], repeated["thinking_since"])
        self.store.select(dict(mode="full_conversation"))
        self.expire()
        self.assertEqual(self.store.read()["status"], "error")

    def test_clear_screen_and_clear_history_have_distinct_effects(self):
        self.store.apply(dict(status="answer", text="Private report", user_text="Private prompt"))
        self.store.apply(dict(status="thinking", run_id="cleared"))
        cleared = self.store.clear()
        self.assertEqual(cleared["status"], "idle")
        self.assertEqual(cleared["last_result"]["text"], "Private report")
        self.assertTrue(cleared["messages"])
        with self.assertRaises(StateError):
            self.store.apply(dict(status="answer", run_id="cleared", text="Old work"))
        erased = self.store.clear(history=True)
        self.assertEqual(erased["messages"], [])
        self.assertIsNone(erased["last_result"])
        with self.assertRaises(StateError):
            self.store.restore()

    def test_duplicate_after_disconnect_remains_idempotent(self):
        event = dict(status="answer", text="Finished", event_id="reconnect")
        first = self.store.apply(event)
        self.store.close()
        self.store = StateStore(self.path)
        self.assertEqual(self.store.apply(event), first)
        with self.assertRaises(StateError):
            self.store.apply({**event, "text": "Changed"})

    def delivery(self, responses):
        self.clock = 1_800_000_000.0
        self.uploads = []
        def uploader(url, payload):
            self.uploads.append(payload)
            return responses.pop(0) if responses else (200, None)
        config = Config(API, IMAGE, webhook_url="https://example.com/private-webhook")
        return WebhookDelivery(self.store, config, uploader=uploader, clock=lambda: self.clock)

    def test_delivery_coalesces_finished_cards_and_skips_thinking(self):
        delivery = self.delivery([])
        self.store.apply(dict(status="thinking"))
        delivery.tick()
        self.assertEqual(self.uploads, [])
        first = self.store.apply(dict(status="answer", text="First"))
        delivery.enqueue(first)
        latest = self.store.apply(dict(status="answer", text="Latest"))
        delivery.tick()
        self.assertEqual(len(self.uploads), 1)
        self.assertTrue(self.uploads[0].startswith(b"\x89PNG"))
        self.assertEqual(delivery.status()["last_accepted"]["revision"], latest["revision"])
        self.assertFalse(delivery.status()["panel_observed"])
        delivery.tick()
        self.assertEqual(len(self.uploads), 1)

    def test_delivery_failure_pending_and_quota_survive_restart(self):
        delivery = self.delivery([(503, None)])
        self.store.apply(dict(status="answer", text="Retry this"))
        delivery.tick()
        self.assertIsNotNone(delivery.status()["pending_revision"])
        self.store.close()
        self.store = StateStore(self.path)
        delivery.store = self.store
        self.clock += 299
        delivery.tick()
        self.assertEqual(len(self.uploads), 1)
        self.clock += 1
        delivery.tick()
        self.assertEqual(len(self.uploads), 2)
        self.assertIsNone(delivery.status()["pending_revision"])

    def test_retry_after_and_permanent_failure_require_distinct_recovery(self):
        delivery = self.delivery([(429, "900"), (422, None), (200, None)])
        self.store.apply(dict(status="answer", text="Quota"))
        delivery.tick()
        self.clock += 899
        delivery.tick()
        self.assertEqual(len(self.uploads), 1)
        self.clock += 1
        delivery.tick()
        self.assertTrue(delivery.status()["blocked"])
        self.clock += 3600
        delivery.tick()
        self.assertEqual(len(self.uploads), 2)
        delivery.retry()
        delivery.tick()
        self.assertEqual(len(self.uploads), 3)

    def test_quota_bounds_repeated_results_and_retries(self):
        delivery = self.delivery([])
        for index in range(12):
            self.store.apply(dict(status="answer", text=f"Result {index}"))
            delivery.tick()
            self.clock += 300
        self.assertEqual(len(self.uploads), 12)
        self.clock -= 1
        self.store.apply(dict(status="answer", text="Wait for quota"))
        delivery.tick()
        self.assertEqual(len(self.uploads), 12)
        self.clock += 1
        delivery.tick()
        self.assertEqual(len(self.uploads), 13)

    def test_history_clear_removes_pending_private_content(self):
        delivery = self.delivery([(503, None)])
        self.store.apply(dict(status="answer", text="Private"))
        delivery.tick()
        cleared = self.store.clear(history=True)
        delivery.tick()
        with self.store.lock:
            pending = delivery._pending()
        self.assertEqual(pending["state"]["text"], "")
        self.assertEqual(pending["state"]["revision"], cleared["revision"])
        self.assertNotIn("Private", json.dumps(pending))

    def test_oversized_image_is_blocked_before_any_upload(self):
        delivery = self.delivery([])
        self.store.apply(dict(status="answer", text="An image that cannot be delivered"))
        with patch("dots_on_paper.delivery.render_image", return_value=b"x" * (MAX_IMAGE_BYTES + 1)):
            delivery.tick()
        self.assertEqual(self.uploads, [])
        self.assertTrue(delivery.status()["blocked"])
        self.assertEqual(delivery.status()["last_attempt"]["http_status"], 422)

    def test_http_upload_uses_raw_png_and_never_follows_redirects(self):
        requests = []
        responses = iter((200, 429, 302))
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                requests.append((self.command, self.headers.get("Content-Type"), self.rfile.read(int(self.headers["Content-Length"]))))
                code = next(responses)
                self.send_response(code)
                self.send_header("Retry-After", "900")
                self.send_header("Location", "/redirect-target")
                self.send_header("Content-Length", "0")
                self.end_headers()
            def do_GET(self):
                requests.append((self.command, None, b""))
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, kwargs=dict(poll_interval=.01), daemon=True)
        thread.start()
        payload = render_image(self.store.apply(dict(status="answer", text="Transport verified")), 800, 480, levels=2)
        try:
            url = f"http://127.0.0.1:{server.server_port}/upload"
            self.assertEqual(upload(url, payload), (200, "900"))
            self.assertEqual(upload(url, payload), (429, "900"))
            self.assertEqual(upload(url, payload), (302, "900"))
            self.assertEqual(requests, [("POST", "image/png", payload)] * 3)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(2)


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = StateStore(Path(self.temp.name) / "state.sqlite3")
        self.config = Config(API, IMAGE)
        self.server = BridgeServer(("127.0.0.1", 0), self.config, self.store)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs=dict(poll_interval=.01), daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.store.close()
        self.temp.cleanup()

    def request(self, path, body=None, token=API, origin=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        if origin:
            headers["Origin"] = origin
        connection = HTTPConnection("127.0.0.1", self.port, timeout=10)
        connection.request("POST" if body is not None else "GET", path, json.dumps(body) if body is not None else None, headers)
        response = connection.getresponse()
        payload = json.loads(response.read())
        connection.close()
        return response.status, payload

    def test_local_pairing_requires_origin_and_is_single_use(self):
        nonce = self.server.pair()
        self.assertEqual(self.request("/api/pair", dict(nonce=nonce), token=None)[0], 403)
        self.assertEqual(self.request("/api/pair", dict(nonce=nonce), token=None, origin="http://127.0.0.1:9999")[0], 403)
        status, value = self.request("/api/pair", dict(nonce=nonce), token=None, origin=f"http://127.0.0.1:{self.port}")
        self.assertEqual((status, value["api_token"]), (200, API))
        self.assertEqual(self.request("/api/pair", dict(nonce=nonce), token=None, origin=f"http://127.0.0.1:{self.port}")[0], 401)

    def test_expired_pairing_does_not_return_credentials(self):
        nonce = self.server.pair()
        self.server.pairing_deadline = 0
        status, value = self.request("/api/pair", dict(nonce=nonce), token=None, origin=f"http://127.0.0.1:{self.port}")
        self.assertEqual(status, 401)
        self.assertNotIn(API, json.dumps(value))

    def test_local_test_is_separate_from_source_receipt(self):
        self.assertEqual(self.request("/api/test-card", dict(text="Useful test"), token=IMAGE)[0], 401)
        self.assertEqual(self.request("/api/test-card", dict(text="Useful test"))[0], 200)
        _, diagnostics = self.request("/api/diagnostics")
        self.assertTrue(diagnostics["local_test_at"])
        self.assertIsNone(diagnostics["source_test_at"])
        rpc = dict(jsonrpc="2.0", id=1, method="tools/call", params=dict(name="publish_dot_reply", arguments=dict(text="Actual tool publication")))
        self.assertEqual(self.request("/mcp", rpc)[0], 200)
        self.assertTrue(self.request("/api/diagnostics")[1]["source_test_at"])

    def test_default_is_settled_and_diagnostics_are_private(self):
        self.store.apply(dict(status="thinking"))
        self.assertFalse(self.request("/api/display-state", token=IMAGE)[1]["animated"])
        self.assertEqual(self.request("/api/diagnostics", token=IMAGE)[0], 401)
        build = self.request("/api/build", token=None)[1]
        self.assertIn("thinking-timeout", build["capabilities"])
        self.assertNotIn(API, json.dumps(build))
        self.assertNotIn("package_path", build)

    def test_clear_requires_an_explicit_history_choice(self):
        self.assertEqual(self.request("/api/clear", {})[0], 400)
        self.assertEqual(self.request("/api/clear", dict(history="false"))[0], 400)
        self.assertEqual(self.request("/api/clear", dict(history=True))[0], 200)
