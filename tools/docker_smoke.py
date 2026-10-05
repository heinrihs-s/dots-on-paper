"""Cold start/restart/recreate an exact image using only a disposable test volume."""
from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import time
from urllib.request import Request, build_opener, ProxyHandler
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    name = "dots-beta-check-" + uuid.uuid4().hex[:12]
    volume = name + "-data"
    environment = {key: value for key, value in os.environ.items() if not key.startswith("DOTS_")}
    api_token, image_token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    environment.update(DOTS_API_TOKEN=api_token, DOTS_IMAGE_TOKEN=image_token)

    def docker(*arguments):
        result = subprocess.run(["docker", *arguments], capture_output=True, text=True, env=environment, timeout=120)
        if result.returncode:
            raise RuntimeError("Docker verification command failed; raw output hidden")
        return result.stdout.strip()

    opener = build_opener(ProxyHandler({}))

    def request(origin, path, body=None, token=api_token):
        headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
        with opener.open(Request(origin + path, data=json.dumps(body).encode() if body is not None else None, headers=headers), timeout=10) as response:
            return response.read()

    def launch():
        docker("run", "-d", "--name", name, "-p", "127.0.0.1::9035", "--env", "DOTS_API_TOKEN", "--env", "DOTS_IMAGE_TOKEN", "--mount", f"type=volume,source={volume},target=/data", args.image)
        origin = "http://" + docker("port", name, "9035/tcp").splitlines()[0]
        ready(origin)
        return origin

    def ready(origin):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                if json.loads(request(origin, "/api/health"))["status"] == "ok":
                    return
            except OSError:
                time.sleep(.2)
        raise RuntimeError("Container did not become healthy")

    docker("volume", "create", "--label", "dots-on-paper.disposable=true", volume)
    try:
        origin = launch()
        check = json.loads(request(origin, "/api/build"))
        assert "thinking-timeout" in check["capabilities"]
        published = json.loads(request(origin, "/api/events", dict(status="answer", text="Disposable container result", event_id="container-proof")))
        assert request(origin, "/image.png?profile=trmnl", token=image_token).startswith(b"\x89PNG")
        docker("restart", name)
        ready(origin)
        assert json.loads(request(origin, "/api/state")) == published
        docker("rm", "--force", name)
        origin = launch()
        assert json.loads(request(origin, "/api/state")) == published
    finally:
        # Exact UUID-owned names; no existing deployment or volume is targeted.
        subprocess.run(["docker", "rm", "--force", name], capture_output=True, timeout=30)
        subprocess.run(["docker", "volume", "rm", volume], capture_output=True, timeout=30)
    print("Exact Docker image passed: non-root cold start, PNG fetch, persisted restart and container replacement using temporary state.")


if __name__ == "__main__":
    main()
