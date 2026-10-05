"""Configuration and separate publishing / display credentials."""
from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]


def default_data_dir() -> Path:
    if (ROOT / "src" / "dots_on_paper").is_dir():
        return ROOT / "data"
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return base / "dots-on-paper"


PROFILES = {
    "trmnl_x": dict(width=1872, height=1404, levels=16),
    "trmnl": dict(width=800, height=480, levels=2),
    "inkplate": dict(width=800, height=600, levels=16),
    "kindle": dict(width=1072, height=1448, levels=16),
    "oep_296": dict(width=296, height=128, levels=2),
    "oep_400": dict(width=400, height=300, levels=2),
}


def init_credentials(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("x", encoding="utf-8") as stream:
            json.dump({"api_token": secrets.token_urlsafe(32), "image_token": secrets.token_urlsafe(32)}, stream, indent=2)
        path.chmod(0o600)


@dataclass
class Config:
    api_token: str
    image_token: str
    host: str = "127.0.0.1"
    port: int = 9035
    public_url: str = "http://127.0.0.1:9035"
    default_profile: str = "trmnl_x"
    refresh_seconds: int = 60
    thinking_refresh_seconds: int = 15
    frame_seconds: int = 5
    trmnl_device_id: str = ""
    trmnl_access_token: str = ""
    allowed_hosts: tuple = ("127.0.0.1", "localhost")
    thinking_timeout_seconds: int = 600
    animate_thinking: bool = False
    webhook_url: str = ""
    webhook_profile: str = "trmnl"

    def __post_init__(self):
        if not all(isinstance(key, str) and len(key) >= 24 and key.isascii() and all(33 <= ord(char) <= 126 for char in key) for key in (self.api_token, self.image_token)) or self.api_token == self.image_token:
            raise ValueError("Use different API and image tokens of at least 24 characters")
        if self.default_profile not in PROFILES:
            raise ValueError("Unknown default profile")
        if not 1 <= self.thinking_timeout_seconds <= 86400:
            raise ValueError("Thinking timeout must be 1–86400 seconds")
        if self.webhook_profile not in ("trmnl", "trmnl_x"):
            raise ValueError("Webhook profile must be trmnl or trmnl_x")
        if self.webhook_url:
            try:
                webhook = urlsplit(self.webhook_url)
                valid = webhook.scheme == "https" and webhook.hostname and not webhook.username and not webhook.password and not webhook.fragment and webhook.port in (None, 443)
            except ValueError:
                valid = False
            if not valid or any(ord(char) < 33 for char in self.webhook_url):
                raise ValueError("Webhook URL must use HTTPS without embedded credentials or a fragment")
        if not 1 <= self.port <= 65535 or self.refresh_seconds < 5 or not 5 <= self.thinking_refresh_seconds <= 3600 or not 2 <= self.frame_seconds <= 3600:
            raise ValueError("Invalid port or refresh interval")
        parts = urlsplit(self.public_url)
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ("", "/"):
            raise ValueError("public_url must be an HTTP(S) origin without credentials, query or path")
        self.public_url = self.public_url.rstrip("/")
        self.allowed_hosts = tuple(set(self.allowed_hosts + (parts.hostname,)))

    @classmethod
    def from_environment(cls, config_file: Path):
        # Env values are convenient for containers; local clients share a private file.
        credentials = {}
        if config_file.exists():
            credentials = json.loads(config_file.read_text(encoding="utf-8"))
        host = os.environ.get("DOTS_HOST", "127.0.0.1")
        port = int(os.environ.get("DOTS_PORT", "9035"))
        return cls(
            api_token=os.environ.get("DOTS_API_TOKEN") or credentials.get("api_token", ""),
            image_token=os.environ.get("DOTS_IMAGE_TOKEN") or credentials.get("image_token", ""),
            host=host, port=port,
            public_url=os.environ.get("DOTS_PUBLIC_URL", f"http://127.0.0.1:{port}"),
            default_profile=os.environ.get("DOTS_PROFILE", "trmnl_x"),
            refresh_seconds=int(os.environ.get("DOTS_REFRESH_SECONDS", "60")),
            thinking_refresh_seconds=int(os.environ.get("DOTS_THINKING_REFRESH_SECONDS", "15")),
            frame_seconds=int(os.environ.get("DOTS_FRAME_SECONDS", "5")),
            trmnl_device_id=os.environ.get("DOTS_TRMNL_DEVICE_ID", ""),
            trmnl_access_token=os.environ.get("DOTS_TRMNL_ACCESS_TOKEN", ""),
            allowed_hosts=tuple(filter(None, os.environ.get("DOTS_ALLOWED_HOSTS", "127.0.0.1,localhost").split(","))),
            thinking_timeout_seconds=int(os.environ.get("DOTS_THINKING_TIMEOUT_SECONDS", "600")),
            animate_thinking=os.environ.get("DOTS_ANIMATE_THINKING", "false").lower() in ("true", "1"),
            webhook_url=os.environ.get("DOTS_TRMNL_WEBHOOK_URL", ""),
            webhook_profile=os.environ.get("DOTS_TRMNL_WEBHOOK_PROFILE", "trmnl"),
        )
