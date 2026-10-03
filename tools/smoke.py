"""Cold-start an installed bridge in temporary storage; no account/device needed."""
from __future__ import annotations

from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    node = shutil.which("node")
    check(bool(node), "Node.js is required for the MCP smoke test")
    with tempfile.TemporaryDirectory(prefix="dots-on-paper-smoke-") as directory:
        data_dir = Path(directory)
        environment = {key: value for key, value in os.environ.items() if not key.startswith("DOTS_") and key != "PYTHONPATH"}
        config_file = data_dir / "credentials.json"
        environment["DOTS_CONFIG_FILE"] = str(config_file)
        initialize = [sys.executable, "-m", "dots_on_paper", "--init", "--data-dir", directory]
        for attempt in range(2):
            result = subprocess.run(initialize, env=environment, cwd=directory, capture_output=True, text=True, timeout=15)
            check(result.returncode == 0, "Installed CLI could not initialize")
            if not attempt:
                original_keys = config_file.read_bytes()
            else:
                check(config_file.read_bytes() == original_keys, "Initialization replaced existing credentials")
        credentials = json.loads(original_keys)
        check(credentials["api_token"] != credentials["image_token"], "Credentials were not independently scoped")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        origin = f"http://127.0.0.1:{port}"
        environment.update({"DOTS_HOST": "127.0.0.1", "DOTS_PORT": str(port), "DOTS_PUBLIC_URL": origin})
        opener = build_opener(ProxyHandler({}))

        def request(path, token=None, body=None):
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = "Bearer " + token
            with opener.open(Request(origin + path, headers=headers, data=json.dumps(body).encode() if body is not None else None), timeout=15) as response:
                return response.read()

        def launch():
            child = subprocess.Popen([sys.executable, "-m", "dots_on_paper", "--data-dir", directory], cwd=directory, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if child.poll() is not None:
                    raise RuntimeError("Installed bridge exited before startup")
                try:
                    check(json.loads(request("/api/health"))["status"] == "ok", "Health failed")
                    return child
                except OSError:
                    time.sleep(.1)
            child.terminate()
            child.wait(timeout=5)
            raise RuntimeError("Installed bridge startup timed out")

        def stop(child):
            child.terminate()
            child.communicate(timeout=10)

        child = launch()
        try:
            initial = json.loads(request("/api/state", credentials["api_token"]))
            check(initial["status"] == "idle" and initial["revision"] == 0, "Cold state was not clean")
            try:
                request("/api/state", credentials["image_token"])
            except HTTPError as error:
                check(error.code == 401, "Image key did not have read-only scope")
            else:
                raise RuntimeError("Image key could read publishing state")
            run_id = "fresh-install-smoke"
            messages = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "fresh-install-smoke", "version": "0.1.0"}}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "set_dot_status", "arguments": {"status": "thinking", "run_id": run_id, "event_id": "smoke-thinking"}}},
                {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "publish_dot_reply", "arguments": {"text": "Fresh-install verification.\n\n- Native image delivered.\n- Credentials stayed private.", "run_id": run_id, "event_id": "smoke-answer", "character": "cool"}}},
            ]
            adapter_environment = {**environment, "DOTS_BRIDGE_URL": origin}
            result = subprocess.run([node, str(ROOT / "src/mcp-stdio.mjs")], env=adapter_environment, cwd=directory, input="".join(json.dumps(item) + "\n" for item in messages), capture_output=True, text=True, timeout=45)
            check(result.returncode == 0, "MCP stdio adapter failed")
            replies = [json.loads(line) for line in result.stdout.splitlines()]
            check(len(replies) == 4 and all("result" in item for item in replies), "MCP exchange was incomplete")
            check(all(not item["result"].get("isError", False) for item in replies), "MCP tool rejected smoke state")
            state = json.loads(request("/api/state", credentials["api_token"]))
            check(state["status"] == "answer" and state["character"] == "cool" and state["revision"] == 2, "Reply did not reach the installed bridge")
            dimensions = []
            for profile, expected_size, levels in (("trmnl_x", (1872, 1404), 16), ("oep_296", (296, 128), 2)):
                payload = request(f"/image.png?profile={profile}&frame=11", credentials["image_token"])
                with Image.open(BytesIO(payload)) as image:
                    check(image.format == "PNG" and image.size == expected_size, "Packaged renderer produced incorrect dimensions")
                    colors = image.convert("L").getcolors(256)
                    check(bool(colors) and len(colors) <= levels, "Packaged renderer produced incorrect grayscale")
                    dimensions.append({"profile": profile, "dimensions": list(image.size), "levels": len(colors)})
        finally:
            stop(child)
        child = launch()
        try:
            restored = json.loads(request("/api/state", credentials["api_token"]))
            check(restored == state, "State did not persist across restart")
        finally:
            stop(child)
    print(json.dumps({"ok": True, "installation": "Installed package; child processes ran outside checkout with no PYTHONPATH", "credentials": "Fresh private keys; initialization idempotent; read-only image scope confirmed", "mcp": "Node stdio initialization, tool discovery, thinking and answer publication passed", "images": dimensions, "persistence": "Latest reply survived process restart", "live_accounts_or_devices": "Not connected"}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        # Do not print raw HTTP/subprocess errors which can contain key-bearing URLs.
        print(json.dumps({"ok": False, "error_type": type(error).__name__, "detail": str(error) if type(error) is RuntimeError else "Smoke test could not complete"}))
        raise SystemExit(1)
