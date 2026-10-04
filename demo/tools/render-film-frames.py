"""Render staged film snapshots with the same renderer used by the bridge.

Called by native-film.mjs. The JSON request supplies fictional states only;
no bridge, private credentials, assistant account, or device is accessed.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
# Export the current checkout, including changes not installed into a wheel yet.
sys.path.insert(0, str(ROOT / "src"))
from dots_on_paper.render import render_image


def main() -> None:
    request = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    frames = []
    for item in request["frames"]:
        payload = render_image(item["state"], 1872, 1404, levels=16, frame=item["frame"])
        frames.append({
            **item,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "uri": "data:image/png;base64," + base64.b64encode(payload).decode("ascii"),
        })
    renderer = ROOT / "src" / "dots_on_paper" / "render.py"
    json.dump({
        "width": 1872, "height": 1404, "levels": 16,
        "source": "src/dots_on_paper/render.py",
        "rendererSha256": hashlib.sha256(renderer.read_bytes()).hexdigest(),
        "frames": frames,
    }, sys.stdout, ensure_ascii=True)


if __name__ == "__main__":
    main()
