"""Content-based build identity works for both source checkouts and wheels."""
from __future__ import annotations

import hashlib
from pathlib import Path

from . import __version__

CAPABILITIES = ("guided-setup", "local-pairing", "thinking-timeout", "retained-result", "clear-history", "webhook-queue", "source-receipts")


def fingerprint(directory: Path | None = None) -> str:
    root = directory or Path(__file__).parent
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file() and path.suffix in (".py", ".html", ".mjs", ".png", ".ttf"))
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        payload = path.read_text(encoding="utf-8").encode() if path.suffix in (".py", ".html", ".mjs") else path.read_bytes()
        digest.update(payload)
    return digest.hexdigest()


def build_info() -> dict:
    return dict(version=__version__, fingerprint=fingerprint(), capabilities=list(CAPABILITIES))
