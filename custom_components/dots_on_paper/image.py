"""Authenticated native image entity for the current e-ink scene."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .api import BridgeError
from .const import (
    CONF_FRAME_INTERVAL,
    CONF_PROFILE,
    DEFAULT_FRAME_INTERVAL,
    DEFAULT_PROFILE,
)
from .coordinator import DotsCoordinator
from .entity import DotsEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([DotsImage(hass, entry.runtime_data)])


class DotsImage(DotsEntity, ImageEntity):
    """Use HA's image proxy; the bridge token stays server-side."""

    _attr_name = "Screen"
    _attr_content_type = "image/png"

    def __init__(self, hass: HomeAssistant, coordinator: DotsCoordinator) -> None:
        DotsEntity.__init__(self, coordinator, "screen")
        ImageEntity.__init__(self, hass)
        self._bytes: bytes | None = None
        self._image_key: tuple[int, int] | None = None
        self._revision = coordinator.data["revision"]
        self._frame = 11 if coordinator.data["status"] == "answer" else 0
        self._frame_interval = max(
            2,
            coordinator.entry.options.get(
                CONF_FRAME_INTERVAL,
                coordinator.entry.data.get(CONF_FRAME_INTERVAL, DEFAULT_FRAME_INTERVAL),
            ),
        )
        self._cancel_animation: Callable[[], None] | None = None
        self._added = False
        self._image_lock = asyncio.Lock()
        self._invalidate_image()

    def _invalidate_image(self) -> None:
        self._bytes = None
        self._image_key = None
        self._cached_image = None
        # HA refetches bytes when this state changes, including when the bridge
        # revision is unchanged during a thinking loop.
        self._attr_image_last_updated = dt_util.utcnow()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._added = True
        self._sync_animation()

    async def async_will_remove_from_hass(self) -> None:
        self._added = False
        self._stop_animation()
        await super().async_will_remove_from_hass()

    @callback
    def _stop_animation(self) -> None:
        if self._cancel_animation is not None:
            self._cancel_animation()
            self._cancel_animation = None

    @callback
    def _sync_animation(self) -> None:
        if not self._added or not self.available or self.coordinator.data["status"] != "thinking":
            self._stop_animation()
        elif self._cancel_animation is None:
            self._cancel_animation = async_track_time_interval(
                self.hass,
                self._advance_frame,
                timedelta(seconds=self._frame_interval),
                cancel_on_shutdown=True,
            )

    @callback
    def _advance_frame(self, _now: datetime) -> None:
        if not self._added or not self.available or self.coordinator.data["status"] != "thinking":
            self._stop_animation()
            return
        if self._image_lock.locked():
            # Finish a slow download before selecting another thinking frame.
            # Status changes still invalidate it immediately in the callback.
            return
        self._frame = (self._frame + 1) % 12
        self._invalidate_image()
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        state = self.coordinator.data
        if self._revision != state["revision"]:
            self._revision = state["revision"]
            self._frame = 11 if state["status"] == "answer" else 0
            self._invalidate_image()
        self._sync_animation()
        super()._handle_coordinator_update()

    async def async_image(self) -> bytes | None:
        async with self._image_lock:
            key = (self.coordinator.data["revision"], self._frame)
            if self._bytes is not None and self._image_key == key:
                return self._bytes
            profile = self.coordinator.entry.options.get(
                CONF_PROFILE, self.coordinator.entry.data.get(CONF_PROFILE, DEFAULT_PROFILE)
            )
            try:
                content = await self.coordinator.bridge.image(profile, frame=key[1])
            except BridgeError:
                return None
            # A completed answer or timer tick can supersede an in-flight frame.
            # Never serve that frame as the image for the newer state.
            if (self.coordinator.data["revision"], self._frame) != key:
                return None
            self._bytes = content
            self._image_key = key
            return content
