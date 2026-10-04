"""Bridge status and answer entities."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .coordinator import DotsCoordinator
from .entity import DotsEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: DotsCoordinator = entry.runtime_data
    async_add_entities([DotsStatus(coordinator), DotsReply(coordinator)])


class DotsStatus(DotsEntity, SensorEntity):
    _attr_name = "Status"
    _attr_icon = "mdi:circle-outline"

    def __init__(self, coordinator: DotsCoordinator) -> None:
        super().__init__(coordinator, "status")

    @property
    def native_value(self) -> str:
        return self.coordinator.data["status"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        state = self.coordinator.data
        return {key: state[key] for key in ("character", "mode", "dot_name", "revision", "updated_at")}


class DotsReply(DotsEntity, SensorEntity, RestoreEntity):
    _attr_name = "Reply"
    _attr_icon = "mdi:message-text-outline"

    def __init__(self, coordinator: DotsCoordinator) -> None:
        super().__init__(coordinator, "reply")
        self._restored_reply: dict[str, Any] = {}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.last_reply is None and (previous := await self.async_get_last_state()):
            self._restored_reply = {
                key: previous.attributes.get(key, {"mode": "last_reply", "messages": []}.get(key, ""))
                for key in ("text", "dot_name", "character", "mode", "messages", "event_id", "run_id", "revision", "title")
            }
            self._restored_reply["title"] = previous.attributes.get("title") or previous.state

    @property
    def _reply(self) -> dict[str, Any]:
        return self.coordinator.last_reply or self._restored_reply

    @property
    def native_value(self) -> str:
        # Full replies belong in attributes, never in the 255-character state.
        return str(self._reply.get("title", ""))[:255] or "No reply yet"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        state = self._reply
        return {
            key: state.get(key, {"mode": "last_reply", "messages": []}.get(key, ""))
            for key in ("text", "dot_name", "character", "mode", "messages", "event_id", "run_id", "revision", "title")
        }
