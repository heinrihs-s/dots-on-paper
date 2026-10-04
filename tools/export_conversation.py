"""Build offline native snapshots for the full-conversation campaign film.

Run this, start ``node demo/serve.mjs``, then run
``node tools/export-conversation.mjs``. Only synthetic display states are used.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dots_on_paper.render import render_image

CONVERSATION = [
    {
        "role": "assistant",
        "content": "Okay, understood. Texting your wife about your date with Paula tonight.",
        "meta": "Draft ready · Waiting for approval",
    },
    {"role": "user", "content": "NOO"},
    {"role": "assistant", "content": "Cancelled. Nothing sent."},
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--character", choices=("artist", "curious", "bookish", "cool"), default="cool")
    parser.add_argument("--output", type=Path, default=ROOT / ".impeccable" / "conversation-frames.json")
    args = parser.parse_args()
    base = {"character": args.character, "dot_name": "heidot", "title": "Conversation"}
    items = [
        {"id": f"thinking-{frame}", "frame": frame, "state": {**base, "status": "thinking", "title": "", "text": ""}}
        for frame in range(12)
    ]
    for count, name in ((1, "draft"), (2, "interruption"), (3, "result")):
        items.append({"id": name, "frame": 11, "state": {**base, "status": "answer", "messages": CONVERSATION[:count]}})
    for item in items:
        payload = render_image(item["state"], 1872, 1404, levels=16, frame=item["frame"])
        item["sha256"] = hashlib.sha256(payload).hexdigest()
        item["uri"] = "data:image/png;base64," + base64.b64encode(payload).decode("ascii")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "source": "src/dots_on_paper/render.py",
        "rendererSha256": hashlib.sha256((ROOT / "src/dots_on_paper/render.py").read_bytes()).hexdigest(),
        "width": 1872, "height": 1404, "levels": 16,
        "duration": 16, "frameSeconds": .5, "resultStartsAt": 9,
        "character": args.character,
        "segments": [
            {"start": 0, "end": 3, "thinking": True},
            {"start": 3, "end": 7, "id": "draft"},
            {"start": 7, "end": 9, "id": "interruption"},
            {"start": 9, "end": 16, "id": "result"},
        ],
        "frames": items,
        "demonstration": "Scripted conversation. No account, calendar, messaging service, or device is accessed.",
    }
    args.output.write_text(json.dumps(metadata, ensure_ascii=True), encoding="utf-8")
    print(f"Native conversation snapshots: {args.output}")


if __name__ == "__main__":
    main()
