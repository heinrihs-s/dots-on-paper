"""Test HA mode selection and state parsing at the integration boundary."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch


class HomeAssistantError(Exception):
    pass


class Entity:
    def __init__(self, coordinator, key) -> None:
        self.coordinator = coordinator
        self.key = key


def module(name: str, **attributes) -> ModuleType:
    value = ModuleType(name)
    value.__dict__.update(attributes)
    return value


def load_modules():
    package = "_dots_ha_modes_under_test"
    directory = Path(__file__).resolve().parents[1] / "custom_components" / "dots_on_paper"
    modules = {
        package: module(package, __path__=[str(directory)]),
        f"{package}.coordinator": module(f"{package}.coordinator", DotsCoordinator=object),
        f"{package}.entity": module(f"{package}.entity", DotsEntity=Entity),
        "aiohttp": module("aiohttp", ClientError=type("ClientError", (Exception,), {})),
        "homeassistant": module("homeassistant", __path__=[]),
        "homeassistant.components": module("homeassistant.components", __path__=[]),
        "homeassistant.components.select": module("homeassistant.components.select", SelectEntity=object),
        "homeassistant.config_entries": module("homeassistant.config_entries", ConfigEntry=object),
        "homeassistant.const": module("homeassistant.const", Platform=SimpleNamespace(IMAGE="image", SENSOR="sensor", SELECT="select")),
        "homeassistant.core": module("homeassistant.core", HomeAssistant=object),
        "homeassistant.exceptions": module("homeassistant.exceptions", HomeAssistantError=HomeAssistantError),
        "homeassistant.helpers": module("homeassistant.helpers", __path__=[]),
        "homeassistant.helpers.entity_platform": module("homeassistant.helpers.entity_platform", AddEntitiesCallback=object),
    }
    loaded = []
    with patch.dict(sys.modules, modules):
        for name in ("api", "select"):
            spec = importlib.util.spec_from_file_location(f"{package}.{name}", directory / f"{name}.py")
            value = importlib.util.module_from_spec(spec)
            sys.modules[f"{package}.{name}"] = value
            spec.loader.exec_module(value)
            loaded.append(value)
    return loaded


def state(**extra):
    return {"status": "answer", "character": "cool", "revision": 4,
            "text": "Cancelled. Nothing sent.", **extra}


class HomeAssistantModeTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.api, cls.select = load_modules()

    def test_older_bridge_state_uses_last_reply_without_history(self) -> None:
        parsed = self.api.validate_state(state())
        self.assertEqual(parsed["mode"], "last_reply")
        self.assertEqual(parsed["messages"], [])

    def test_supplied_conversation_survives_state_parsing(self) -> None:
        messages = [{"role": "user", "content": "NOO"},
                    {"role": "assistant", "content": "Cancelled. Nothing sent.", "meta": "Reply"}]
        parsed = self.api.validate_state(state(mode="full_conversation", messages=messages))
        self.assertEqual(parsed["mode"], "full_conversation")
        self.assertEqual(parsed["messages"], messages)
        self.assertIsNot(parsed["messages"], messages)

    def test_incompatible_modes_and_unbounded_turns_are_rejected(self) -> None:
        for extra in ({"mode": "automatic"}, {"messages": {}},
                      {"messages": [{"role": "system", "content": "Hidden"}]},
                      {"messages": [{"role": "user", "content": " "}]},
                      {"messages": [{"role": "user", "content": "x"}] * 21},
                      {"messages": [{"role": "user", "content": "x" * 12000}] * 3},
                      {"messages": [{"role": "user", "content": "x", "meta": "x" * 121}]}):
            with self.subTest(extra=extra):
                with self.assertRaises(self.api.BridgeError):
                    self.api.validate_state(state(**extra))

    async def test_mode_select_changes_settings_and_skips_current_selection(self) -> None:
        coordinator = SimpleNamespace(data={"mode": "last_reply"}, set_mode=AsyncMock())
        entity = self.select.DotsDisplayMode(coordinator)
        self.assertEqual(entity.current_option, "last_reply")
        await entity.async_select_option("last_reply")
        coordinator.set_mode.assert_not_awaited()
        await entity.async_select_option("full_conversation")
        coordinator.set_mode.assert_awaited_once_with("full_conversation")
        with self.assertRaises(HomeAssistantError):
            await entity.async_select_option("automatic")

    async def test_mode_select_reports_bridge_failure(self) -> None:
        coordinator = SimpleNamespace(data={"mode": "last_reply"},
                                      set_mode=AsyncMock(side_effect=self.api.BridgeError("Bridge unavailable")))
        entity = self.select.DotsDisplayMode(coordinator)
        with self.assertRaisesRegex(HomeAssistantError, "Bridge unavailable"):
            await entity.async_select_option("full_conversation")

    async def test_mode_patch_is_authenticated_and_contains_only_the_setting(self) -> None:
        requests = []

        class Response:
            status = 200

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                pass

            async def json(self):
                return state(mode="full_conversation", messages=[])

        class Session:
            def request(self, method, url, **kwargs):
                requests.append((method, url, kwargs))
                return Response()

        bridge = self.api.DotsBridge(Session(), "http://example.invalid/bridge", "fixture-token")
        result = await bridge.set_mode("full_conversation")
        self.assertEqual(result["mode"], "full_conversation")
        method, url, arguments = requests[0]
        self.assertEqual((method, url), ("PATCH", "http://example.invalid/bridge/api/settings"))
        self.assertEqual(arguments["json"], {"mode": "full_conversation"})
        self.assertEqual(arguments["headers"], {"Authorization": "Bearer fixture-token"})
        self.assertFalse(arguments["allow_redirects"])


if __name__ == "__main__":
    unittest.main()
