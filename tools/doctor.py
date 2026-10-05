"""Read-only installation and bridge diagnostics; never print keys or replies."""
from __future__ import annotations

import argparse
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler, Request

ROOT = Path(__file__).resolve().parents[1]


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        return None


class DiagnosisError(Exception):
    pass


def check(condition: bool, detail: str) -> None:
    if not condition:
        raise DiagnosisError(detail)


def request(url: str, *, token: str | None = None, body: dict | None = None) -> bytes:
    headers = {"Accept": "application/json, text/event-stream"}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    if body is not None:
        headers.update({"Content-Type": "application/json", "MCP-Protocol-Version": "2025-11-25"})
    opener = build_opener(NoRedirect, ProxyHandler({}))
    with opener.open(Request(url, data=json.dumps(body).encode() if body is not None else None, headers=headers), timeout=15) as response:
        payload = response.read(8_000_001)
    check(len(payload) <= 8_000_000, "Bridge response is too large")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Check local files and configuration without contacting the bridge")
    parser.add_argument("--mcp", action="store_true", help="Also require Node and verify the optional stdio source adapter")
    parser.add_argument("--url", help="Bridge origin; defaults to configured DOTS_PUBLIC_URL or loopback")
    parser.add_argument("--config", type=Path, default=Path(os.environ.get("DOTS_CONFIG_FILE", ROOT / "data/credentials.json")))
    args = parser.parse_args()
    results: list[dict[str, str]] = []

    def probe(name, action):
        try:
            detail = action()
        except DiagnosisError as error:
            results.append({"check": name, "status": "failed", "detail": str(error)})
            return None
        except HTTPError as error:
            results.append({"check": name, "status": "failed", "detail": f"Bridge returned HTTP {error.code}"})
            return None
        except Exception as error:
            # HTTP/file exceptions can carry key-bearing URLs or response data.
            results.append({"check": name, "status": "failed", "detail": type(error).__name__})
            return None
        results.append({"check": name, "status": "passed", "detail": str(detail)})
        return detail

    def python_runtime():
        check(sys.version_info >= (3, 11), "Python 3.11+ is required")
        return sys.version.split()[0]

    def renderer():
        from PIL import Image
        from dots_on_paper import render
        from importlib.metadata import version
        pillow_version = version("Pillow")
        major, minor = (int(value) for value in pillow_version.split(".")[:2])
        check((major, minor) >= (11, 2) and major < 13, "Install the declared Pillow version with tools/setup.py")
        assets = Path(render.__file__).resolve().parent / "assets"
        for filename in ("beret-dot.png", "curious-dot.png", "bookish-dot.png", "cool-dot.png"):
            with Image.open(assets / filename) as image:
                image.verify()
        check((assets / "Figtree.ttf").is_file(), "Packaged Figtree font is missing")
        return f"Pillow {pillow_version}; four characters and font present"

    def node_runtime():
        node = shutil.which("node")
        check(bool(node), "Node.js 22+ is required for the local MCP adapter")
        result = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=10)
        check(result.returncode == 0 and result.stdout.startswith("v"), "Cannot run Node.js")
        check(int(result.stdout.strip().split(".")[0][1:]) >= 22, "Node.js 22+ is required")
        return result.stdout.strip()

    probe("Python", python_runtime)
    expected_build = None

    def installed_build():
        nonlocal expected_build
        environment = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
        script = "import json; import dots_on_paper; from dots_on_paper.build import build_info; print(json.dumps({**build_info(), 'package_path': dots_on_paper.__file__}))"
        with tempfile.TemporaryDirectory(prefix="dots-doctor-") as directory:
            result = subprocess.run([sys.executable, "-c", script], cwd=directory, env=environment, capture_output=True, text=True, timeout=15)
        check(result.returncode == 0, "Installed build metadata is missing. Run python tools/setup.py, then restart the bridge")
        installed = json.loads(result.stdout)
        from dots_on_paper.build import fingerprint
        expected_build = fingerprint(ROOT / "src/dots_on_paper")
        check(installed.get("fingerprint") == expected_build, "Installed package differs from this checkout. Run python tools/setup.py, then restart; keep the same data directory")
        return f"{installed['version']}; {installed['fingerprint'][:12]}; {installed['package_path']}"

    probe("Installed build", installed_build)
    probe("Renderer assets", renderer)
    node_ok = probe("Node MCP runtime", node_runtime) if args.mcp else None
    config = None

    def credentials():
        nonlocal config
        from dots_on_paper.config import Config
        check(args.config.is_file() or bool(os.environ.get("DOTS_API_TOKEN") and os.environ.get("DOTS_IMAGE_TOKEN")), "Initialize keys with tools/setup.py or run.ps1 -Init")
        try:
            config = Config.from_environment(args.config)
        except (ValueError, TypeError, AttributeError) as error:
            raise DiagnosisError("Credentials or bridge settings are invalid; check the private configuration and DOTS variables") from error
        return "Publishing and read-only image credentials valid; values hidden"

    probe("Private configuration", credentials)
    if not args.offline and config is not None:
        origin = (args.url or config.public_url).rstrip("/")
        def bridge_url():
            parsed = urlsplit(origin)
            check(parsed.scheme in ("http", "https") and bool(parsed.hostname) and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment, "Use an HTTP(S) bridge URL without credentials or query")
            parsed.port
            return "Configured bridge URL is valid"

        if probe("Bridge URL", bridge_url) is None:
            print(json.dumps({"ok": False, "mode": "read-only live", "checks": results}, ensure_ascii=True, indent=2))
            return 1

        def health():
            value = json.loads(request(origin + "/api/health"))
            check(value.get("status") == "ok", "Bridge health was not successful")
            build = json.loads(request(origin + "/api/build"))
            check(build.get("fingerprint") == expected_build, "Running bridge differs from this checkout. Reinstall and restart it")
            return f"Bridge reachable; running build {build['fingerprint'][:12]} matches checkout"

        def state():
            value = json.loads(request(origin + "/api/state", token=config.api_token))
            check(value.get("status") in ("idle", "thinking", "answer", "error") and isinstance(value.get("revision"), int), "Incompatible bridge state")
            return "Publishing authentication accepted; reply content hidden"

        def image():
            from PIL import Image
            from dots_on_paper.config import PROFILES
            expected = PROFILES[config.default_profile]
            payload = request(origin + f"/image.png?profile={config.default_profile}&frame=0", token=config.image_token)
            with Image.open(BytesIO(payload)) as picture:
                check(picture.format == "PNG" and picture.size == (expected["width"], expected["height"]), "Unexpected image format or dimensions")
                colors = picture.convert("L").getcolors(256)
                check(bool(colors) and len(colors) <= expected["levels"], "Unexpected grayscale levels")
            return f"{config.default_profile}; {expected['width']} × {expected['height']} PNG"

        def http_mcp():
            value = json.loads(request(origin + "/mcp", token=config.api_token, body={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}))
            names = {tool["name"] for tool in value.get("result", {}).get("tools", [])}
            check(names == {"publish_dot_reply", "set_dot_status", "get_dot_state"}, "Expected three display tools")
            return "All three tools available over authenticated HTTP"

        def stdio_mcp():
            environment = {**os.environ, "DOTS_BRIDGE_URL": origin, "DOTS_API_TOKEN": config.api_token}
            messages = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "dots-doctor", "version": "0.1.0"}}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            ]
            result = subprocess.run([shutil.which("node"), str(ROOT / "src/mcp-stdio.mjs")], input="".join(json.dumps(message) + "\n" for message in messages), env=environment, cwd=ROOT, capture_output=True, text=True, timeout=35)
            check(result.returncode == 0, "MCP adapter could not start; check Node and bridge configuration")
            replies = [json.loads(line) for line in result.stdout.splitlines()]
            check(len(replies) == 2 and all("result" in item for item in replies), "MCP adapter did not initialize and list tools")
            check(replies[0]["result"].get("protocolVersion") == "2025-11-25", "Unexpected MCP protocol")
            check(len(replies[1]["result"].get("tools", [])) == 3, "MCP tool list was incomplete")
            return "Node adapter → bridge initialization and tool discovery passed"

        probe("Bridge health", health)
        probe("Publishing authentication", state)
        probe("Read-only display image", image)
        probe("HTTP MCP", http_mcp)
        def delivery():
            value = json.loads(request(origin + "/api/diagnostics", token=config.api_token))
            source = "MCP publication received" if value.get("source_test_at") else "No MCP publication received yet"
            webhook = value.get("webhook", {})
            hardware = "upload accepted" if webhook.get("last_accepted") else "BYOS requested an image" if value.get("byos_requested_at") else "no hardware receipt"
            return f"{source}; {hardware}; panel observation still requires the named device"

        probe("Source and delivery receipts", delivery)
        if node_ok is not None:
            probe("Stdio MCP", stdio_mcp)
    failures = sum(result["status"] == "failed" for result in results)
    print(json.dumps({"ok": failures == 0, "mode": "offline" if args.offline else "read-only live", "checks": results}, ensure_ascii=True, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
