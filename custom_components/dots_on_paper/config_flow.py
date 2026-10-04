"""Configure and authenticate a local Dots on Paper bridge."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BridgeAuthError, BridgeError, DotsBridge, bridge_identity, normalize_url
from .const import (
    CONF_API_TOKEN,
    CONF_BASE_URL,
    CONF_FRAME_INTERVAL,
    CONF_POLL_INTERVAL,
    CONF_PROFILE,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_FRAME_INTERVAL,
    DEFAULT_PROFILE,
    DOMAIN,
    PROFILES,
)


def _profile_schema(defaults: dict[str, Any]) -> dict[Any, Any]:
    return {
        vol.Required(CONF_PROFILE, default=defaults.get(CONF_PROFILE, DEFAULT_PROFILE)): selector.SelectSelector(
            selector.SelectSelectorConfig(options=list(PROFILES))
        ),
        vol.Required(
            CONF_POLL_INTERVAL, default=defaults.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
        ): vol.All(vol.Coerce(int), vol.Range(min=2, max=120)),
        vol.Required(
            CONF_FRAME_INTERVAL, default=defaults.get(CONF_FRAME_INTERVAL, DEFAULT_FRAME_INTERVAL)
        ): vol.All(vol.Coerce(int), vol.Range(min=2, max=120)),
    }


class DotsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                user_input[CONF_BASE_URL] = normalize_url(user_input[CONF_BASE_URL])
                if not user_input[CONF_PROFILE].strip():
                    raise ValueError("Missing profile")
                bridge = DotsBridge(
                    async_get_clientsession(self.hass),
                    user_input[CONF_BASE_URL],
                    user_input[CONF_API_TOKEN],
                )
                await bridge.state()
                # Validate that the selected profile can render, rather than
                # letting setup succeed with a permanently broken image entity.
                await bridge.image(user_input[CONF_PROFILE])
            except BridgeAuthError:
                errors["base"] = "invalid_auth"
            except BridgeError:
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "invalid_url"
            else:
                await self.async_set_unique_id(bridge_identity(user_input[CONF_BASE_URL]))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Dots on Paper", data=user_input)
        defaults = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BASE_URL, default=defaults.get(CONF_BASE_URL, "http://localhost:9035")): str,
                    vol.Required(CONF_API_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                    ),
                    **_profile_schema(defaults),
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            bridge = DotsBridge(
                async_get_clientsession(self.hass),
                entry.data[CONF_BASE_URL],
                user_input[CONF_API_TOKEN],
            )
            try:
                await bridge.state()
            except BridgeAuthError:
                errors["base"] = "invalid_auth"
            except BridgeError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_API_TOKEN: user_input[CONF_API_TOKEN]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                    )
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return DotsOptionsFlow(config_entry)


class DotsOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            bridge = DotsBridge(
                async_get_clientsession(self.hass),
                self._entry.data[CONF_BASE_URL],
                self._entry.data[CONF_API_TOKEN],
            )
            try:
                await bridge.image(user_input[CONF_PROFILE])
            except BridgeAuthError:
                errors["base"] = "invalid_auth"
            except BridgeError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="", data=user_input)
        defaults = {**self._entry.data, **self._entry.options, **(user_input or {})}
        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(_profile_schema(defaults)), errors=errors
        )
