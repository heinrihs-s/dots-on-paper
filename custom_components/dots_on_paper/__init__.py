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
    DISPLAY_MODES,
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
    vol.Optional("mode"): vol.In(DISPLAY_MODES),
    vol.Optional("user_text"): vol.All(cv.string, vol.Length(min=1, max=12000)),
    vol.Optional("messages"): vol.All(
        vol.Length(min=1, max=20),
        [vol.Schema({
            vol.Required("role"): vol.In(("user", "assistant")),
            vol.Required("content"): vol.All(cv.string, vol.Length(min=1, max=12000)),
            vol.Optional("meta"): vol.All(cv.string, vol.Length(max=120)),
        })],
    ),
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
        if "user_text" in call.data and "messages" in call.data:
            raise HomeAssistantError("Use user_text or messages, not both")
        if "messages" in call.data:
            messages = call.data["messages"]
            if payload["status"] != "answer":
                raise HomeAssistantError("A conversation snapshot requires an answer")
            if any(not item["content"].strip() for item in messages) or sum(len(item["content"]) for item in messages) > 24000:
                raise HomeAssistantError("Conversation messages must contain text and fit within 24000 characters")
            if messages[-1]["role"] != "assistant" or messages[-1]["content"] != payload["text"]:
                raise HomeAssistantError("The last conversation message must match the reply text")
        if "user_text" in call.data and (
            payload["status"] not in ("thinking", "answer") or not call.data["user_text"].strip()
        ):
            raise HomeAssistantError("User text requires thinking or an answer")
        for key in ("event_id", "run_id", "mode", "user_text", "messages"):
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
