"""Core integration tests with a real HTTP server, SQLite, renderer and MCP adapter."""
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

from PIL import Image

from dots_on_paper.config import Config, PROFILES
from dots_on_paper.server import BridgeServer, state_frame
from dots_on_paper.state import StateError, StateStore

API_KEY = "publish-test-" + "p" * 32
IMAGE_KEY = "image-test-" + "i" * 32
ROOT = Path(__file__).resolve().parents[1]


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = StateStore(Path(self.temp.name) / "state.sqlite3")
        self.config = Config(API_KEY, IMAGE_KEY)
        self.server = BridgeServer(("127.0.0.1", 0), self.config, self.store)
        self.port = self.server.server_address[1]
        self.config.public_url = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.store.close()
        self.temp.cleanup()

    def request(self, method, path, data=None, token=API_KEY, headers=None, raw=None):
        supplied = {"Accept": "application/json, text/event-stream"}
        if token is not None:
            supplied["Authorization"] = "Bearer " + token
        if data is not None or raw is not None:
            supplied["Content-Type"] = "application/json"
        supplied.update(headers or {})
        body = raw if raw is not None else json.dumps(data).encode() if data is not None else None
        connection = HTTPConnection("127.0.0.1", self.port, timeout=20)
        connection.request(method, path, body=body, headers=supplied)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def event(self, **fields):
        status, _, payload = self.request("POST", "/api/events", fields)
        return status, json.loads(payload)

    def rpc(self, method, params=None, ident=1, **kwargs):
        request = dict(jsonrpc="2.0", method=method, params=params or {})
        if ident is not None:
            request["id"] = ident
        status, _, payload = self.request("POST", "/mcp", request, **kwargs)
        return status, json.loads(payload) if payload else None

    def test_health_is_public_but_contains_no_reply_or_keys(self):
        self.event(status="answer", text="Private reply")
        status, _, payload = self.request("GET", "/api/health", token=None)
        self.assertEqual(status, 200)
        self.assertEqual(set(json.loads(payload)), {"status", "version"})
        self.assertNotIn(b"Private reply", payload)
        self.assertNotIn(API_KEY.encode(), payload)

    def test_state_requires_publishing_key(self):
        for token in (None, "wrong", IMAGE_KEY, "é"):
            self.assertEqual(self.request("GET", "/api/state", token=token)[0], 401)
        self.assertEqual(self.request("GET", "/api/state?key=" + API_KEY, token=None)[0], 401)

    def test_image_key_is_read_only(self):
        self.assertEqual(self.request("GET", "/image.png?profile=oep_296", token=IMAGE_KEY)[0], 200)
        self.assertEqual(self.request("GET", "/image.png?profile=oep_296&key=" + IMAGE_KEY, token=None)[0], 200)
        self.assertEqual(self.request("GET", "/image.png?key=%C3%A9", token=None)[0], 401)
        self.assertEqual(self.request("POST", "/api/events", {"status": "answer", "text": "x"}, token=IMAGE_KEY)[0], 401)
        self.assertEqual(self.request("PATCH", "/api/settings", {"character": "cool"}, token=IMAGE_KEY)[0], 401)
        self.assertEqual(self.rpc("tools/list", token=IMAGE_KEY)[0], 401)

    def test_reply_and_character_selection_preserve_event(self):
        _, answer = self.event(status="answer", text="A real answer", dot_name="Olive", event_id="reply1")
        status, _, payload = self.request("PATCH", "/api/settings", {"character": "bookish"})
        selected = json.loads(payload)
        self.assertEqual(status, 200)
        self.assertEqual(selected["character"], "bookish")
        self.assertEqual(selected["text"], "A real answer")
        self.assertEqual(selected["event_id"], answer["event_id"])
        self.assertEqual(selected["run_id"], answer["run_id"])
        self.assertEqual(selected["revision"], answer["revision"] + 1)

    def test_retries_are_idempotent_and_conflicting_id_is_rejected(self):
        data = dict(status="answer", text="Same answer", event_id="stable-id")
        _, first = self.event(**data)
        _, duplicate = self.event(**data)
        self.assertEqual(first, duplicate)
        self.assertEqual(self.event(**{**data, "text": "Changed"})[0], 409)

    def test_concurrent_retries_write_once(self):
        payload = dict(status="answer", text="One reply", event_id="concurrent-id")
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.event(**payload), range(16)))
        self.assertTrue(all(status == 200 for status, _ in results))
        self.assertEqual(self.store.read()["revision"], 1)

    def test_stale_completion_cannot_replace_new_run(self):
        self.event(status="thinking", run_id="old")
        self.event(status="thinking", run_id="new")
        self.assertEqual(self.event(status="answer", run_id="old", text="Stale")[0], 409)
        self.assertEqual(self.event(status="answer", run_id="new", text="Current")[0], 200)
        self.assertEqual(self.event(status="thinking", run_id="new")[0], 409)
        self.assertEqual(self.store.read()["text"], "Current")

    def test_stale_completion_after_history_pruning_is_rejected(self):
        self.store.apply(dict(status="thinking", run_id="old"))
        for i in range(1003):
            self.store.apply(dict(status="answer", text=f"Answer {i}"))
        with self.assertRaises(StateError) as failure:
            self.store.apply(dict(status="answer", run_id="old", text="Stale"))
        self.assertEqual(failure.exception.status, 409)

    def test_explicit_completion_requires_thinking_but_standalone_answer_works(self):
        self.assertEqual(self.event(status="answer", run_id="unknown", text="Hello")[0], 409)
        self.assertEqual(self.event(status="answer", text="Hello")[0], 200)

    def test_validation_rejects_surrogates_empty_answers_and_unknown_fields(self):
        bad = [dict(status="answer", text=""), dict(status="answer", text="x", secret="x"),
               dict(status="answer", text="\ud800"), dict(status="answer", text="x", character="unknown"),
               dict(status="thinking", run_id="bad/id"), dict(status="answer", text="x" * 12001),
               dict(status="answer", text="hello\x00")]
        for data in bad:
            self.assertEqual(self.request("POST", "/api/events", data)[0], 400)
        self.assertEqual(self.store.read()["revision"], 0)

    def test_body_content_type_limits_and_bad_json(self):
        self.assertEqual(self.request("POST", "/api/events", raw=b"{}", headers={"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.request("POST", "/api/events", raw=b"x" * 65537)[0], 413)
        self.assertEqual(self.request("POST", "/api/events", raw=b"{broken")[0], 400)
        self.assertEqual(self.request("POST", "/api/events", raw=b'{"status":NaN}')[0], 400)

    def test_invalid_host_origin_and_query_are_controlled(self):
        self.assertEqual(self.request("GET", "/api/state", headers={"Host": "attacker.test"})[0], 403)
        self.assertEqual(self.request("POST", "/mcp", {}, headers={"Origin": "https://attacker.test"})[0], 403)
        self.assertEqual(self.request("GET", "/api/state?" + "&".join(f"k{i}=x" for i in range(21)))[0], 400)
        self.assertEqual(self.request("GET", "/image.png?profile=trmnl&profile=kindle")[0], 400)

    def test_profiles_and_png_bmp_dimensions_quantization(self):
        for profile, settings in PROFILES.items():
            status, _, payload = self.request("GET", "/image.png?profile=" + profile)
            self.assertEqual(status, 200)
            image = Image.open(BytesIO(payload))
            self.assertEqual(image.size, (settings["width"], settings["height"]))
            self.assertLessEqual(len(image.convert("L").getcolors(256)), settings["levels"])
        status, headers, payload = self.request("GET", "/image.bmp?width=400&height=300&levels=2")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "image/bmp")
        self.assertEqual(Image.open(BytesIO(payload)).size, (400, 300))

    def test_image_options_etag_and_private_cache(self):
        for query in ("width=12&height=12", "width=2401&height=100", "width=100", "levels=3", "frame=12", "profile=unknown"):
            self.assertEqual(self.request("GET", "/image.png?" + query)[0], 400)
        status, headers, _ = self.request("GET", "/image.png?profile=oep_296")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.request("GET", "/image.png?profile=oep_296", headers={"If-None-Match": headers["ETag"]})[0], 304)
        self.assertEqual(self.request("GET", "/image.png?profile=oep_296", token=None, headers={"If-None-Match": headers["ETag"]})[0], 401)

    def test_automatic_frames_loop_thinking_and_settle_answers(self):
        old = (datetime.now(timezone.utc) - timedelta(seconds=72)).isoformat()
        state = dict(status="thinking", updated_at=old)
        self.assertEqual(state_frame(state, 5), 2)
        state["status"] = "answer"
        self.assertEqual(state_frame(state, 5), 11)
        state["status"] = "idle"
        self.assertEqual(state_frame(state, 5), 0)
        self.event(status="thinking", run_id="auto-frame")
        status, _, automatic = self.request("GET", "/image.png?profile=oep_296")
        self.assertEqual(status, 200)
        self.assertEqual(automatic, self.request("GET", "/image.png?profile=oep_296&frame=0")[2])

    def test_mcp_handshake_versions_and_notifications(self):
        for version in ("2025-11-25", "2025-06-18", "2025-03-26"):
            status, value = self.rpc("initialize", {"protocolVersion": version, "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}})
            self.assertEqual(status, 200)
            self.assertEqual(value["result"]["protocolVersion"], version)
        self.assertEqual(self.rpc("notifications/initialized", ident=None), (202, None))
        self.assertEqual(self.rpc("ping")[1]["result"], {})
        self.assertEqual(self.rpc("tools/list", headers={"MCP-Protocol-Version": "bad"})[0], 400)
        self.assertEqual(self.request("GET", "/mcp")[0], 405)
        self.assertEqual(self.request("GET", "/mcp", headers={"MCP-Protocol-Version": "bad"})[0], 400)
        self.assertEqual(self.request("POST", "/mcp", {"jsonrpc": "2.0", "id": 1, "result": {}})[0], 202)

    def test_mcp_schema_and_real_answer_delivery(self):
        tools = self.rpc("tools/list")[1]["result"]["tools"]
        self.assertEqual({tool["name"] for tool in tools}, {"set_dot_status", "publish_dot_reply", "get_dot_state"})
        self.rpc("tools/call", {"name": "set_dot_status", "arguments": {"status": "thinking", "run_id": "mcp-turn"}})
        status, value = self.rpc("tools/call", {"name": "publish_dot_reply", "arguments": {"text": "Delivered through MCP", "run_id": "mcp-turn", "dot_name": "My actual dot"}})
        self.assertEqual(status, 200)
        self.assertFalse(value["result"]["isError"])
        self.assertEqual(self.store.read()["text"], "Delivered through MCP")
        for invalid in ({"text": ""}, {"text": "secret", "unknown": 1}):
            result = self.rpc("tools/call", {"name": "publish_dot_reply", "arguments": invalid})[1]["result"]
            self.assertTrue(result["isError"])

    def test_node_adapter_against_actual_bridge(self):
        messages = [dict(jsonrpc="2.0", id=1, method="initialize", params=dict(protocolVersion="2025-11-25", capabilities={}, clientInfo=dict(name="integration-test", version="1"))),
                    dict(jsonrpc="2.0", method="notifications/initialized"),
                    dict(jsonrpc="2.0", id=2, method="tools/list"),
                    dict(jsonrpc="2.0", id=3, method="tools/call", params=dict(name="set_dot_status", arguments=dict(status="thinking", run_id="stdio-turn"))),
                    dict(jsonrpc="2.0", id=4, method="tools/call", params=dict(name="publish_dot_reply", arguments=dict(text="Actual adapter delivery", run_id="stdio-turn", character="cool"))),
                    dict(jsonrpc="2.0", id=5, method="tools/call", params=dict(name="get_dot_state", arguments={}))]
        env = {**os.environ, "DOTS_API_TOKEN": API_KEY, "DOTS_BRIDGE_URL": self.config.public_url}
        proc = subprocess.run(["node", str(ROOT / "src" / "mcp-stdio.mjs")], input="\n".join(json.dumps(message) for message in messages) + "\n", text=True, capture_output=True, env=env, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        output = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual([entry["id"] for entry in output], [1, 2, 3, 4, 5])
        state = output[-1]["result"]["structuredContent"]
        self.assertEqual(state["text"], "Actual adapter delivery")
        self.assertEqual(state["character"], "cool")
        self.assertNotIn(API_KEY, proc.stdout + proc.stderr)

    def test_trmnl_byos_requires_existing_device_auth(self):
        self.assertEqual(self.request("GET", "/api/display", token=None)[0], 503)
        self.assertEqual(self.request("GET", "/api/setup", token=None)[0], 403)
        self.config.trmnl_device_id = "AA:BB:CC:DD:EE:FF"
        self.config.trmnl_access_token = "device-secret-test"
        self.assertEqual(self.request("GET", "/api/display", token=None, headers={"ID": self.config.trmnl_device_id, "Access-Token": "wrong"})[0], 401)
        status, _, payload = self.request("GET", "/api/display", token=None, headers={"ID": self.config.trmnl_device_id, "Access-Token": self.config.trmnl_access_token})
        display = json.loads(payload)
        self.assertEqual(status, 200)
        self.assertFalse(display["update_firmware"])
        query = parse_qs(urlsplit(display["image_url"]).query)
        self.assertEqual(query["key"], [IMAGE_KEY])
        self.assertEqual(display["refresh_rate"], 60)
        self.assertNotIn(API_KEY, display["image_url"])

    def test_sqlite_state_survives_reopening(self):
        self.event(status="answer", text="Persisted answer", character="curious")
        path = Path(self.temp.name) / "state.sqlite3"
        with_store = StateStore(path)
        try:
            self.assertEqual(with_store.read()["text"], "Persisted answer")
            self.assertEqual(with_store.read()["character"], "curious")
        finally:
            with_store.close()

    def test_config_rejects_shared_short_or_nonascii_keys(self):
        for args in ((API_KEY, API_KEY), ("short", IMAGE_KEY), ("é" * 30, IMAGE_KEY), ("a" * 30 + "\n", IMAGE_KEY)):
            with self.assertRaises(ValueError):
                Config(*args)


if __name__ == "__main__":
    unittest.main()
