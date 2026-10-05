"""Authenticated REST, stateless Streamable HTTP MCP and e-ink image endpoints."""
from __future__ import annotations

import hashlib
import json
import logging
import secrets
import threading
import time
import ipaddress
from contextlib import nullcontext
from collections import OrderedDict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

from . import __version__
from .config import Config, PROFILES
from .build import build_info
from .delivery import WebhookDelivery
from .render import render_image
from .state import CHARACTERS, DISPLAY_MODES, MAX_MESSAGES, StateError, StateStore

LOGGER = logging.getLogger(__name__)
MAX_BODY = 65536
PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26")
ASSET_ROOT = Path(__file__).parent / "assets"
ASSETS = {"beret-dot.png", "curious-dot.png", "bookish-dot.png", "cool-dot.png", "Figtree.ttf"}
FRAME_COUNT = 12
DISPLAY_BUDGETS = {"trmnl_x": 1200, "trmnl": 420, "inkplate": 600, "kindle": 1000, "oep_296": 90, "oep_400": 220}


def state_frame(state: dict, seconds: int) -> int:
    if state["status"] == "answer":
        return FRAME_COUNT - 1
    try:
        updated = datetime.fromisoformat(state["updated_at"])
        elapsed = max(0, (datetime.now(timezone.utc) - updated).total_seconds())
    except (ValueError, TypeError, KeyError):
        elapsed = 0
    step = int(elapsed / seconds)
    if state["status"] == "thinking":
        return step % FRAME_COUNT
    return 0


def tool_schema() -> list[dict]:
    common = {
        "character": {"type": "string", "enum": list(CHARACTERS), "description": "Optional; otherwise keep the selected character."},
        "dot_name": {"type": "string", "maxLength": 80},
        "title": {"type": "string", "maxLength": 120},
        "mode": {"type": "string", "enum": list(DISPLAY_MODES), "description": "Optional retained display mode: show only the latest answer or the explicitly published conversation."},
        "source": {"type": "string", "maxLength": 80, "description": "A short source label, such as your assistant or daily brief."},
        "run_id": {"type": "string", "pattern": "^[A-Za-z0-9_.:-]{1,128}$", "description": "Use the same unique ID for thinking and completion to reject stale replies."},
        "event_id": {"type": "string", "pattern": "^[A-Za-z0-9_.:-]{1,128}$", "description": "Optional stable ID for safe retries of identical events."},
    }
    user_text = {"type": "string", "minLength": 1, "maxLength": 12000,
                 "description": "Optional user message explicitly authorized for display. The bridge does not capture chat automatically."}
    messages = dict(type="array", minItems=1, maxItems=MAX_MESSAGES,
                    description="Optional replacement conversation, at most 24,000 content characters. The last turn must be assistant content matching text. Cannot be combined with user_text.",
                    items=dict(type="object", properties=dict(role=dict(type="string", enum=["user", "assistant"]),
                               content=dict(type="string", minLength=1, maxLength=12000), meta=dict(type="string", maxLength=120)),
                               required=["role", "content"], additionalProperties=False))
    return [
        dict(name="publish_dot_reply", description="Put your actual completed answer on the user's connected e-ink display. Optional user_text or messages supplies authorized conversation turns. This writes externally visible text. Publish only content authorized by the user; never private reasoning, credentials or an invented response.",
             inputSchema=dict(type="object", properties={**common, "text": dict(type="string", minLength=1, maxLength=12000), "user_text": user_text, "messages": messages}, required=["text"], additionalProperties=False),
             annotations=dict(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)),
        dict(name="set_dot_status", description="Set the connected dot display to thinking, idle or error. Use a fresh run_id for thinking and the same ID when publishing its answer. Displayed error text must not include secrets.",
             inputSchema=dict(type="object", properties={**common, "status": dict(type="string", enum=["idle", "thinking", "error"]), "text": dict(type="string", maxLength=12000), "user_text": {**user_text, "description": "Optional authorized user message for a thinking run only."}}, required=["status"], additionalProperties=False),
             annotations=dict(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)),
        dict(name="get_dot_state", description="Read the selected character, display mode, status, latest reply and explicitly published conversation. No account or device credentials are returned.",
             inputSchema=dict(type="object", properties={}, additionalProperties=False),
             annotations=dict(readOnlyHint=True, idempotentHint=True, openWorldHint=False)),
    ]


class BridgeServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 16

    def __init__(self, address, config: Config, store: StateStore):
        self.config = config
        self.store = store
        self.image_lock = threading.RLock()
        self.image_cache = OrderedDict()
        self.device_frame_lock = threading.Lock()
        self.device_frame_revision = None
        self.device_frame_index = 0
        self.pairing_lock = threading.Lock()
        self.pairing_nonce = ""
        self.pairing_deadline = 0
        self.config_file = None
        self.build = build_info()
        self.store.thinking_timeout_seconds = config.thinking_timeout_seconds
        self.delivery = WebhookDelivery(store, config) if config.webhook_url else None
        super().__init__(address, BridgeHandler)
        if self.delivery:
            self.delivery.start()

    def server_close(self):
        if self.delivery:
            self.delivery.close()
        super().server_close()

    def pair(self) -> str:
        with self.pairing_lock:
            self.pairing_nonce = secrets.token_urlsafe(32)
            self.pairing_deadline = time.monotonic() + 600
            return self.pairing_nonce

    def diagnostics(self) -> dict:
        metadata = self.store.metadata()
        return dict(build={**self.build, "package_path": str(Path(__file__).parent)},
                    local_test_at=metadata.get("local_test_at"), source_test_at=metadata.get("source_test_at"),
                    source_test_kind="MCP tool publication" if metadata.get("source_test_at") else None,
                    image_fetched_at=metadata.get("image_fetched_at"), byos_requested_at=metadata.get("byos_requested_at"),
                    panel_observed=False, thinking_timeout_seconds=self.config.thinking_timeout_seconds,
                    animate_thinking=self.config.animate_thinking, display_budgets=DISPLAY_BUDGETS,
                    webhook=self.delivery.status() if self.delivery else dict(configured=False, panel_observed=False))

    def device_frame(self, state: dict, advance: bool = True) -> int:
        """Advance the enrolled device once per poll, independent of sleep phase."""
        if state["status"] == "thinking" and not self.config.animate_thinking:
            return 0
        if state["status"] != "thinking" or not self.config.animate_thinking:
            return state_frame(state, self.config.frame_seconds)
        with self.device_frame_lock:
            if self.device_frame_revision != state["revision"]:
                self.device_frame_revision = state["revision"]
                self.device_frame_index = 0
            frame = self.device_frame_index
            if advance:
                self.device_frame_index = (frame + 1) % FRAME_COUNT
            return frame

    def image(self, state: dict, width: int, height: int, levels: int, fmt: str, frame: int):
        key = (state["revision"], width, height, levels, fmt, frame)
        # One renderer at a time bounds transient memory and prevents duplicate work.
        with self.image_lock:
            if key not in self.image_cache:
                budget = next((DISPLAY_BUDGETS[name] for name, profile in PROFILES.items() if (profile['width'], profile['height']) == (width, height)), max(60, round(width * height / 900)))
                payload = render_image({**state, "display_budget": min(1200, budget)}, width, height, levels=levels, format=fmt, frame=frame)
                self.image_cache[key] = (payload, '"' + hashlib.sha256(payload).hexdigest() + '"')
            self.image_cache.move_to_end(key)
            while len(self.image_cache) > 16:
                self.image_cache.popitem(last=False)
            return self.image_cache[key]

    def handle_error(self, request, client_address):
        LOGGER.error("A connection failed; no request data was logged")


class BridgeHandler(BaseHTTPRequestHandler):
    server: BridgeServer
    server_version = "DotsOnPaper/0.1"

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, format, *args):
        # Request lines contain scoped image keys. Never log paths, headers or bodies.
        pass

    def respond(self, status: int, payload: bytes = b"", content_type="application/json", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' blob:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def json(self, status: int, data, extra=None):
        self.respond(status, json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8"), extra=extra)

    def valid_host(self):
        try:
            host = urlsplit("//" + self.headers.get("Host", "")).hostname
            origin = self.headers.get("Origin")
            origin_host = urlsplit(origin).hostname if origin else None
            if host not in self.server.config.allowed_hosts or (origin and origin_host not in self.server.config.allowed_hosts):
                self.json(403, {"error": "Host or Origin is not allowed"})
                return False
            return True
        except ValueError:
            self.json(400, {"error": "Invalid Host or Origin"})
            return False

    def auth(self, image=False, query=None):
        config = self.server.config
        bearer = self.headers.get("Authorization", "")
        token = bearer[7:] if bearer.startswith("Bearer ") else ""
        accepted = bool(token) and token.isascii() and secrets.compare_digest(token, config.api_token)
        if image:
            key = (query or {}).get("key", "")
            accepted = accepted or (bool(token) and token.isascii() and secrets.compare_digest(token, config.image_token)) or (bool(key) and key.isascii() and secrets.compare_digest(key, config.image_token))
        if not accepted:
            self.json(401, {"error": "A valid bearer token is required"}, {"WWW-Authenticate": 'Bearer realm="dots-on-paper"'})
        return accepted

    def route(self):
        parts = urlsplit(self.path)
        if len(parts.query) > 4096:
            raise StateError("Query is too long")
        try:
            query = parse_qs(parts.query, keep_blank_values=True, max_num_fields=20)
        except ValueError:
            raise StateError("Too many or invalid query fields")
        if any(len(values) != 1 for values in query.values()):
            raise StateError("Duplicate query fields are not supported")
        return parts.path, {key: value[0] for key, value in query.items()}

    def body(self):
        if self.headers.get("Transfer-Encoding"):
            raise StateError("Chunked request bodies are not supported")
        if self.headers.get_content_type() != "application/json":
            raise StateError("Content-Type must be application/json", 415)
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            raise StateError("Invalid Content-Length")
        if not 0 <= length <= MAX_BODY:
            raise StateError("JSON request body must be at most 64 KiB", 413)
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise StateError("Incomplete request body")
        try:
            return json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError, UnicodeError, RecursionError):
            raise StateError("Invalid JSON")

    def image_options(self, query):
        allowed = {"key", "profile", "width", "height", "levels", "frame"}
        if set(query) - allowed:
            raise StateError("Unknown image option")
        profile = query.get("profile", self.server.config.default_profile)
        if profile not in PROFILES:
            raise StateError("Unknown image profile")
        options = dict(PROFILES[profile])
        if ("width" in query) != ("height" in query):
            raise StateError("Custom dimensions require both width and height")
        try:
            for key in ("width", "height", "levels"):
                if key in query:
                    options[key] = int(query[key])
            options["frame"] = int(query["frame"]) if "frame" in query else None
        except ValueError:
            raise StateError("Image dimensions, levels and frame must be integers")
        if not 64 <= options["width"] <= 2400 or not 64 <= options["height"] <= 2400 or options["width"] * options["height"] > 8000000:
            raise StateError("Dimensions must be 64–2400 with at most 8 million pixels")
        if options["levels"] not in (2, 16) or (options["frame"] is not None and not 0 <= options["frame"] <= 11):
            raise StateError("levels must be 2 or 16; frame must be 0–11")
        return options

    def device_auth(self):
        config = self.server.config
        device_id, access_token = self.headers.get("ID", ""), self.headers.get("Access-Token", "")
        if not config.trmnl_device_id or not config.trmnl_access_token:
            self.json(503, {"error": "TRMNL BYOS is not configured"})
            return False
        if not secrets.compare_digest(device_id.encode(), config.trmnl_device_id.encode()) or not secrets.compare_digest(access_token.encode(), config.trmnl_access_token.encode()):
            self.json(401, {"error": "Unknown TRMNL device or access token"})
            return False
        return True

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self.valid_host():
            return
        try:
            path, query = self.route()
            if path == "/api/health":
                return self.json(200, dict(status="ok", version=__version__))
            if path == "/api/build":
                return self.json(200, self.server.build)
            if path == "/":
                page = (Path(__file__).parent / "web.html").read_bytes()
                page = page.replace(b"__DOTS_FRAME_SECONDS__", str(int(self.server.config.frame_seconds)).encode("ascii"))
                page = page.replace(b"__DOTS_ANIMATE__", b"true" if self.server.config.animate_thinking else b"false")
                return self.respond(200, page, "text/html; charset=utf-8")
            if path.startswith("/assets/") and path[8:] in ASSETS:
                name = path[8:]
                return self.respond(200, (ASSET_ROOT / name).read_bytes(), "font/ttf" if name.endswith(".ttf") else "image/png")
            if path == "/mcp":
                if self.auth():
                    if self.headers.get("MCP-Protocol-Version", "2025-03-26") not in PROTOCOLS:
                        return self.json(400, {"error": "Unsupported MCP protocol version"})
                    return self.json(405, {"error": "This stateless MCP endpoint accepts POST"}, {"Allow": "POST"})
                return
            if path in ("/api/state", "/api/profiles"):
                if self.auth():
                    return self.json(200, self.server.store.read() if path.endswith("state") else PROFILES)
                return
            if path == "/api/diagnostics":
                if self.auth():
                    return self.json(200, self.server.diagnostics())
                return
            if path == "/api/client-config":
                if not self.auth():
                    return
                if not self.server.config_file:
                    raise StateError("Use the checkout plugin with DOTS_API_TOKEN supplied privately; no local credentials file is available", 409)
                adapter = str(Path(__file__).parent / "mcp-stdio.mjs")
                return self.json(200, dict(mcpServers={"dots-on-paper": dict(command="node", args=[adapter], env=dict(
                    DOTS_BRIDGE_URL=f"http://127.0.0.1:{self.server.server_address[1]}", DOTS_CONFIG_FILE=str(self.server.config_file)))}))
            if path == "/api/display-state":
                if set(query) - {"key"}:
                    raise StateError("Unknown display-state option")
                if self.auth(image=True, query=query):
                    state = self.server.store.read()
                    config = self.server.config
                    animated = state["status"] == "thinking" and config.animate_thinking
                    return self.json(200, dict(status=state["status"], mode=state["mode"], revision=state["revision"],
                        animated=animated, frame=state_frame(state, config.frame_seconds) if animated else 11 if state["status"] == "answer" else 0,
                        frame_count=FRAME_COUNT, frame_seconds=config.frame_seconds,
                        next_poll_seconds=config.frame_seconds if animated else config.refresh_seconds))
                return
            if path in ("/image.png", "/image.bmp"):
                if not self.auth(image=True, query=query):
                    return
                options = self.image_options(query)
                state = self.server.store.read()
                if options["frame"] is None or state["status"] != "thinking":
                    options["frame"] = state_frame(state, self.server.config.frame_seconds) if state["status"] != "thinking" or self.server.config.animate_thinking else 0
                payload, etag = self.server.image(state, **options, fmt="PNG" if path.endswith("png") else "BMP")
                if self.command != "HEAD":
                    self.server.store.mark("image_fetched_at")
                if self.headers.get("If-None-Match") == etag:
                    return self.respond(304, extra={"ETag": etag})
                return self.respond(200, payload, "image/png" if path.endswith("png") else "image/bmp", {"ETag": etag})
            if path == "/api/display":
                if not self.device_auth():
                    return
                config = self.server.config
                state = self.server.store.read()
                if self.command != "HEAD":
                    self.server.store.mark("byos_requested_at")
                frame = self.server.device_frame(state, advance=self.command != "HEAD")
                image_query = urlencode(dict(profile=config.default_profile, key=config.image_token, frame=frame))
                return self.json(200, dict(status=0, image_url=f"{config.public_url}/image.png?{image_query}",
                    filename=f"dots-{state['revision']}-{frame}.png",
                    refresh_rate=config.thinking_refresh_seconds if state["status"] == "thinking" and config.animate_thinking else config.refresh_seconds,
                    update_firmware=False, reset_firmware=False))
            if path == "/api/setup":
                return self.json(403, {"error": "Automatic device enrollment is disabled. Configure your existing BYOS device ID and token."})
            self.json(404, {"error": "Not found"})
        except StateError as error:
            self.json(error.status, {"error": str(error)})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            LOGGER.error("A display request failed; no request data was logged")
            self.json(500, {"error": "Display request failed"})

    def do_PATCH(self):
        self.mutate("PATCH")

    def do_POST(self):
        self.mutate("POST")

    def mutate(self, method):
        if not self.valid_host():
            return
        try:
            path, query = self.route()
            if query:
                raise StateError("Mutation endpoints do not accept query parameters")
            if method == "POST" and path == "/api/pair":
                return self.pair_browser(self.body())
            if not self.auth():
                return
            if method == "POST" and path == "/api/test-card":
                value = self.body()
                if not isinstance(value, dict) or set(value) - {"text"}:
                    raise StateError("Test card accepts only text")
                state = self.server.store.apply(dict(status="answer", title="Reply", source="Local test", text=value.get("text", "Site review finished. Two broken links found. Report ready.")))
                self.server.store.mark("local_test_at")
                return self.json(200, state)
            if method == "POST" and path == "/api/clear":
                value = self.body()
                if not isinstance(value, dict) or set(value) != {"history"} or not isinstance(value["history"], bool):
                    raise StateError("Clear requires a history boolean")
                with self.server.delivery.lock if self.server.delivery else nullcontext():
                    return self.json(200, self.server.store.clear(value["history"]))
            if method == "POST" and path in ("/api/restore", "/api/delivery/retry"):
                if self.body() != {}:
                    raise StateError("This action accepts an empty JSON object")
                if path == "/api/restore":
                    return self.json(200, self.server.store.restore())
                if not self.server.delivery:
                    raise StateError("Webhook delivery is not configured", 409)
                self.server.delivery.retry()
                return self.json(200, self.server.delivery.status())
            if method == "PATCH" and path == "/api/settings":
                return self.json(200, self.server.store.select(self.body()))
            if method == "POST" and path == "/api/events":
                return self.json(200, self.server.store.apply(self.body()))
            if method == "POST" and path == "/mcp":
                return self.mcp(self.body())
            self.json(404, {"error": "Not found"})
        except StateError as error:
            self.json(error.status, {"error": str(error)})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            LOGGER.error("A mutation failed; no request data was logged")
            self.json(500, {"error": "Request failed"})

    def pair_browser(self, value):
        origin = self.headers.get("Origin", "")
        if not ipaddress.ip_address(self.client_address[0]).is_loopback or origin != "http://" + self.headers.get("Host", ""):
            raise StateError("Pairing requires the browser opened locally by the launcher", 403)
        if not isinstance(value, dict) or set(value) != {"nonce"} or not isinstance(value["nonce"], str) or not value["nonce"].isascii() or len(value["nonce"]) > 128:
            raise StateError("Invalid local pairing request")
        with self.server.pairing_lock:
            valid = self.server.pairing_nonce and time.monotonic() <= self.server.pairing_deadline and secrets.compare_digest(value["nonce"], self.server.pairing_nonce)
            if not valid:
                raise StateError("Pairing expired or already used. Restart with --open, or connect using your private credentials file", 401)
            self.server.pairing_nonce = ""
        return self.json(200, dict(api_token=self.server.config.api_token))

    def mcp(self, request):
        if self.headers.get("MCP-Protocol-Version", "2025-03-26") not in PROTOCOLS:
            return self.json(400, {"error": "Unsupported MCP protocol version"})
        ident = request.get("id") if isinstance(request, dict) else None

        def result(value):
            self.json(200, dict(jsonrpc="2.0", id=ident, result=value))

        def error(code, message):
            self.json(200, dict(jsonrpc="2.0", id=ident, error=dict(code=code, message=message)))

        if isinstance(request, dict) and request.get("jsonrpc") == "2.0" and "method" not in request and "id" in request and ("result" in request) != ("error" in request):
            return self.respond(202)
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
            return error(-32600, "Invalid JSON-RPC request")
        if isinstance(ident, bool) or (ident is not None and not isinstance(ident, (str, int))):
            return error(-32600, "Invalid JSON-RPC id")
        if "id" not in request:
            return self.respond(202)
        method, params = request["method"], request.get("params", {})
        if not isinstance(params, dict):
            return error(-32602, "params must be an object")
        if method == "initialize":
            proposed = params.get("protocolVersion")
            return result(dict(protocolVersion=proposed if proposed in PROTOCOLS else PROTOCOLS[0],
                capabilities=dict(tools={}), serverInfo=dict(name="dots-on-paper", version=__version__),
                instructions="Publish actual answers only when authorized. Text is displayed on physical screens. Keep secrets and private reasoning out of tools."))
        if method == "ping":
            return result({})
        if method == "tools/list":
            return result(dict(tools=tool_schema()))
        if method != "tools/call":
            return error(-32601, "Method not found")
        name, arguments = params.get("name"), params.get("arguments", {})
        if not isinstance(arguments, dict):
            return error(-32602, "Tool arguments must be an object")
        try:
            if name == "get_dot_state":
                if arguments:
                    raise StateError("get_dot_state accepts no arguments")
                state = self.server.store.read()
            elif name == "publish_dot_reply":
                if "status" in arguments:
                    raise StateError("publish_dot_reply does not accept status")
                state = self.server.store.apply({"source": "MCP", **arguments, "status": "answer"})
                self.server.store.mark("source_test_at")
            elif name == "set_dot_status":
                if arguments.get("status") not in ("idle", "thinking", "error"):
                    raise StateError("status must be idle, thinking or error")
                state = self.server.store.apply(arguments)
            else:
                return error(-32602, "Unknown tool")
            return result(dict(content=[dict(type="text", text=json.dumps(state, ensure_ascii=False))], structuredContent=state, isError=False))
        except StateError as failure:
            return result(dict(content=[dict(type="text", text=str(failure))], isError=True))
