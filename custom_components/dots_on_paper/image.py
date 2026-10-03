"""Authenticated native image entity for the current e-ink scene."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import BridgeError
from .const import CONF_PROFILE, DEFAULT_PROFILE
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
        self._image_revision: int | None = None
        self._update_timestamp()

    def _update_timestamp(self) -> None:
        state = self.coordinator.data
        parsed: datetime | None = dt_util.parse_datetime(state.get("updated_at", ""))
        self._attr_image_last_updated = parsed or dt_util.utcnow()

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._image_revision != self.coordinator.data["revision"]:
            self._bytes = None
            self._cached_image = None
            self._update_timestamp()
        super()._handle_coordinator_update()

    async def async_image(self) -> bytes | None:
        revision = self.coordinator.data["revision"]
        if self._bytes is not None and self._image_revision == revision:
            return self._bytes
        profile = self.coordinator.entry.options.get(
            CONF_PROFILE, self.coordinator.entry.data.get(CONF_PROFILE, DEFAULT_PROFILE)
        )
        try:
            content = await self.coordinator.bridge.image(profile)
        except BridgeError:
            return None
        # Don't cache a frame under a revision which changed during download.
        if self.coordinator.data["revision"] == revision:
            self._bytes = content
            self._image_revision = revision
        return content
