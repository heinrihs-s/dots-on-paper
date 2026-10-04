"""Small authenticated client for the local Dots on Paper bridge."""

from __future__ import annotations

import asyncio
from hashlib import sha256
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import aiohttp

from .const import CHARACTERS, STATUSES


class BridgeError(Exception):
    """A bridge request failed without including private response data."""


class BridgeAuthError(BridgeError):
    """The bridge rejected authentication."""


def normalize_url(value: str) -> str:
    """Accept HTTP origins or base paths, without embedded credentials."""
    parts = urlsplit(value.strip())
    if (
        parts.scheme not in ("http", "https")
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
    ):
        raise ValueError("Enter an HTTP or HTTPS bridge URL without credentials")
    try:
        parts.port
    except ValueError as err:
        raise ValueError("Invalid bridge port") from err
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", "")
    )


def bridge_identity(base_url: str) -> str:
    """Keep endpoint identity stable without exposing its URL in unique IDs."""
    return sha256(base_url.encode()).hexdigest()[:20]


def validate_state(value: Any) -> dict[str, Any]:
    """Reject incompatible state responses before creating HA entities."""
    if not isinstance(value, dict):
        raise BridgeError("Invalid bridge state")
    if value.get("status") not in STATUSES or value.get("character") not in CHARACTERS:
        raise BridgeError("Unsupported bridge state")
    revision = value.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise BridgeError("Invalid bridge revision")
    result: dict[str, Any] = {
        "status": value["status"],
        "character": value["character"],
        "revision": revision,
    }
    for key in ("dot_name", "title", "text", "event_id", "run_id", "updated_at"):
        field = value.get(key, "")
        if field is None and key in ("event_id", "run_id"):
            field = ""
        if not isinstance(field, str):
            raise BridgeError("Invalid bridge state field")
        result[key] = field
    return result


class DotsBridge:
    """Use Home Assistant's shared aiohttp session; never put API keys in URLs."""

    def __init__(
        self, session: aiohttp.ClientSession, base_url: str, api_token: str
    ) -> None:
        self.session = session
        self.base_url = normalize_url(base_url)
        self._headers = {"Authorization": f"Bearer {api_token}"}

    async def _json(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            async with asyncio.timeout(15):
                async with self.session.request(
                    method,
                    f"{self.base_url}{path}",
                    headers=self._headers,
                    json=payload,
                    allow_redirects=False,
                ) as response:
                    if response.status in (401, 403):
                        raise BridgeAuthError("Bridge authentication failed")
                    if response.status >= 300:
                        raise BridgeError(f"Bridge returned HTTP {response.status}")
                    return validate_state(await response.json())
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise BridgeError("Unable to read bridge state") from err

    async def state(self) -> dict[str, Any]:
        return await self._json("GET", "/api/state")

    async def publish(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._json("POST", "/api/events", payload)

    async def set_character(self, character: str) -> dict[str, Any]:
        return await self._json("PATCH", "/api/settings", {"character": character})

    async def image(self, profile: str, *, frame: int | None = None) -> bytes:
        params: dict[str, str | int] = {"profile": profile}
        if frame is not None:
            params["frame"] = frame
        try:
            async with asyncio.timeout(20):
                async with self.session.get(
                    f"{self.base_url}/image.png",
                    params=params,
                    headers=self._headers,
                    allow_redirects=False,
                ) as response:
                    if response.status in (401, 403):
                        raise BridgeAuthError("Bridge authentication failed")
                    if response.status >= 300:
                        raise BridgeError(f"Image returned HTTP {response.status}")
                    if response.content_length and response.content_length > 8_000_000:
                        raise BridgeError("Bridge image is too large")
                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.content.iter_chunked(65536):
                        total += len(chunk)
                        if total > 8_000_000:
                            raise BridgeError("Bridge image is too large")
                        chunks.append(chunk)
                    content = b"".join(chunks)
                    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
                        raise BridgeError("Bridge did not return a PNG image")
                    return content
        except (aiohttp.ClientError, TimeoutError) as err:
            raise BridgeError("Unable to fetch bridge image") from err
