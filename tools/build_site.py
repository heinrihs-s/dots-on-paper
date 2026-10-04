"""Build the public static showcase without reading bridge data or credentials."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dots_on_paper.render import _mascot, _source_image, render_image

OUTPUT = ROOT / "site" / "dist" / "dotsonpaper"
REPLIES = {
    "reminders": "Here are your reminders:\n\n- Tonight: Date with Paula.\n- Tomorrow morning: Breakfast with Amy.\n- Lunch: With your wife.\n\nYour calendar needs a lawyer.",
}
MESSAGES = [
    {"role": "assistant", "content": "Okay, understood. Texting your wife about your date with Paula tonight.", "meta": "Draft ready · Waiting for approval"},
    {"role": "user", "content": "NOO"},
    {"role": "assistant", "content": "Cancelled. Nothing sent."},
]
ASSETS = {"artist": "beret-dot.png", "curious": "curious-dot.png", "bookish": "bookish-dot.png", "cool": "cool-dot.png"}


def copy_text(source: Path, destination: Path) -> None:
    # Git normalizes text in the deployment checkout. Match those exact bytes
    # even when the build runs on Windows with CRLF source assets.
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")


def main() -> None:
    assets = OUTPUT / "assets"
    frames = assets / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    # Remove only known, retired showcase assets from a previous build.
    for path in [assets / "dot-noo.mp4", *(frames / f"{character}-noo.png" for character in ASSETS)]:
        path.unlink(missing_ok=True)
    for name in ("index.html", "styles.css", "site.js"):
        copy_text(ROOT / "site" / name, OUTPUT / name)
    for name in ("logo-cool.svg", "icon-cool.svg"):
        copy_text(ROOT / "brand" / name, assets / name)
    shutil.copy2(ROOT / "demo/assets/Figtree.ttf", assets / "Figtree.ttf")
    copy_text(ROOT / "demo/assets/Figtree-LICENSE.txt", assets / "Figtree-LICENSE.txt")
    Image.open(ROOT / "brand" / "header-paper-v2.png").save(assets / "header-paper.webp", "WEBP", quality=88, method=6)
    for character, filename in ASSETS.items():
        # The source bodies are blank sprites; use the native renderer for the
        # eyes/glasses too, retaining the asset's existing alpha silhouette.
        portrait = Image.new("L", (160, 160), 255)
        _mascot(portrait, character, (0, 0, 160, 160), "answer", 11)
        portrait = portrait.convert("RGBA")
        _, alpha = _source_image(character)
        portrait.putalpha(alpha.resize((160, 160), Image.Resampling.LANCZOS))
        portrait.save(assets / f"{character}.png", optimize=True)
        state = {"character": character, "dot_name": "heidot", "title": "", "status": "thinking", "text": ""}
        for frame in range(12):
            (frames / f"{character}-thinking-{frame}.png").write_bytes(render_image(state, 960, 720, levels=16, frame=frame))
        for example, text in REPLIES.items():
            result = {**state, "status": "answer", "title": "Reply", "text": text}
            (frames / f"{character}-{example}.png").write_bytes(render_image(result, 960, 720, levels=16, frame=11))
        for turn in range(1, 4):
            result = {**state, "status": "answer", "title": "Conversation", "messages": MESSAGES[:turn], "text": ""}
            content = render_image(result, 960, 720, levels=16, frame=11)
            (frames / f"{character}-conversation-{turn}.png").write_bytes(content)
            if turn == 3:
                (frames / f"{character}-conversation.png").write_bytes(content)
    for name in ("dot-reminders.mp4", "dot-conversation.mp4"):
        shutil.copy2(ROOT / "campaign" / "media" / name, assets / name)
    metadata = {
        "source": "https://github.com/heinrihs-s/dots-on-paper",
        "canonical": "https://heinrihs.org/dotsonpaper/",
        "renderer_sha256": hashlib.sha256((ROOT / "src/dots_on_paper/render.py").read_bytes()).hexdigest(),
        "demonstration": "Fictional replies; offline native renderer; 0.5-second thinking snapshots; no account, bridge data, calendar or device accessed.",
        "files": {path.relative_to(OUTPUT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(OUTPUT.rglob("*")) if path.is_file() and path.name != "build.json"},
    }
    (OUTPUT / "build.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    total = sum(path.stat().st_size for path in OUTPUT.rglob("*") if path.is_file())
    print(f"Built {len(metadata['files'])} public files ({total:,} bytes) at {OUTPUT}")


if __name__ == "__main__":
    main()
