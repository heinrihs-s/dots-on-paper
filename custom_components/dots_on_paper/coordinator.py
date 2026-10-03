"""Coordinate bridge state and publish one event for each new answer."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BridgeAuthError, BridgeError, DotsBridge, bridge_identity
from .const import (
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    EVENT_DOT_REPLY,
)

_LOGGER = logging.getLogger(__name__)


class DotsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll state; serialise local commands; suppress replayed answers."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, bridge: DotsBridge) -> None:
        interval = entry.options.get(
            CONF_POLL_INTERVAL, entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=max(2, interval)),
            always_update=False,
        )
        self.entry = entry
        self.bridge = bridge
        self.bridge_id = bridge_identity(bridge.base_url)
        self._revision: int | None = None
        self._event_id: str | None = None
        self.last_reply: dict[str, Any] | None = None
        self._command_lock = asyncio.Lock()

    def _accept_state(self, state: dict[str, Any], *, emit_reply: bool = True) -> None:
        revision = state["revision"]
        # The first refresh is a snapshot, not a newly received reply. A repeated
        # poll or a character-only command must not replay an old automation.
        is_new = (
            self._revision is not None
            and revision > self._revision
            and state["event_id"] != self._event_id
        )
        self._revision = revision
        self._event_id = state["event_id"]
        if state["status"] == "answer":
            self.last_reply = dict(state)
        if emit_reply and is_new and state["status"] == "answer":
            self.hass.bus.async_fire(
                EVENT_DOT_REPLY,
                {"entry_id": self.entry.entry_id, **state},
            )

    async def _async_update_data(self) -> dict[str, Any]:
        async with self._command_lock:
            try:
                state = await self.bridge.state()
            except BridgeAuthError as err:
                raise ConfigEntryAuthFailed("Bridge authentication failed") from err
            except BridgeError as err:
                raise UpdateFailed(str(err)) from err
            self._accept_state(state)
            return state

    async def publish(
        self, payload: dict[str, Any], *, emit_reply: bool = True
    ) -> dict[str, Any]:
        async with self._command_lock:
            state = await self.bridge.publish(payload)
            self._accept_state(state, emit_reply=emit_reply)
            self.async_set_updated_data(state)
            return state

    async def set_character(self, character: str) -> None:
        async with self._command_lock:
            state = await self.bridge.set_character(character)
            # Settings preserve event_id. If an external answer arrived before
            # this PATCH, its genuinely new event still deserves one HA event.
            self._accept_state(state)
            self.async_set_updated_data(state)
