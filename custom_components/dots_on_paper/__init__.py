"""Home Assistant integration for the Dots on Paper bridge."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import BridgeError, DotsBridge
from .const import (
    CHARACTERS,
    CONF_API_TOKEN,
    CONF_BASE_URL,
    DOMAIN,
    PLATFORMS,
    STATUSES,
)
from .coordinator import DotsCoordinator

_COMMON_FIELDS = {
    vol.Required("entry_id"): cv.string,
    vol.Optional("character"): vol.In(CHARACTERS),
    vol.Optional("dot_name"): vol.All(cv.string, vol.Length(max=80)),
    vol.Optional("title"): vol.All(cv.string, vol.Length(max=120)),
    vol.Optional("event_id"): vol.All(cv.string, vol.Match(r"^[A-Za-z0-9_.:-]{1,128}$")),
    vol.Optional("run_id"): vol.All(cv.string, vol.Match(r"^[A-Za-z0-9_.:-]{1,128}$")),
}
_ANSWER_SCHEMA = vol.Schema(
    {**_COMMON_FIELDS, vol.Required("text"): vol.All(cv.string, vol.Length(min=1, max=12000))}
)
_STATE_SCHEMA = vol.Schema(
    {
        **_COMMON_FIELDS,
        vol.Required("status"): vol.In(STATUSES),
        vol.Optional("text"): vol.All(cv.string, vol.Length(max=12000)),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Keep actions registered even while a configured bridge is unavailable."""
    hass.data.setdefault(DOMAIN, {})

    async def handle(call: ServiceCall, *, answer: bool) -> None:
        coordinator: DotsCoordinator | None = hass.data[DOMAIN].get(call.data["entry_id"])
        if coordinator is None:
            raise HomeAssistantError("The selected Dots on Paper bridge is not loaded")
        current = coordinator.data
        payload: dict[str, Any] = {
            "status": "answer" if answer else call.data["status"],
            "character": call.data.get("character", current["character"]),
            "dot_name": call.data.get("dot_name", current["dot_name"]),
            "title": call.data.get("title", "Your dot replied" if answer else ""),
            "text": call.data.get("text", ""),
        }
        if payload["status"] == "answer" and not payload["text"].strip():
            raise HomeAssistantError("An answer needs reply text")
        for key in ("event_id", "run_id"):
            if key in call.data:
                payload[key] = call.data[key]
        try:
            await coordinator.publish(payload)
        except BridgeError as err:
            raise HomeAssistantError(str(err)) from err

    async def show_answer(call: ServiceCall) -> None:
        await handle(call, answer=True)

    async def set_state(call: ServiceCall) -> None:
        await handle(call, answer=False)

    hass.services.async_register(DOMAIN, "show_answer", show_answer, schema=_ANSWER_SCHEMA)
    hass.services.async_register(DOMAIN, "set_state", set_state, schema=_STATE_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    bridge = DotsBridge(
        async_get_clientsession(hass), entry.data[CONF_BASE_URL], entry.data[CONF_API_TOKEN]
    )
    coordinator = DotsCoordinator(hass, entry, bridge)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        raise
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
