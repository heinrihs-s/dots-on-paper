"""Exercise HA image lifecycle logic without claiming a live HA runtime check."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


@dataclass
class Timer:
    callback: object
    interval: object
    active: bool = True


class BridgeError(Exception):
    pass


class Bridge:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []
        self.started = asyncio.Event()
        self.release: asyncio.Event | None = None
        self.fail = False

    async def image(self, profile: str, *, frame: int) -> bytes:
        self.calls.append((profile, frame))
        self.started.set()
        if self.release is not None:
            await self.release.wait()
        if self.fail:
            raise BridgeError("Image unavailable")
        return f"image-{frame}".encode()


class Entity:
    def __init__(self, coordinator, _key) -> None:
        self.coordinator = coordinator
        self.writes = 0

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        pass

    async def async_will_remove_from_hass(self) -> None:
        pass

    def async_write_ha_state(self) -> None:
        self.writes += 1

    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()


class ImageEntity:
    def __init__(self, hass) -> None:
        self.hass = hass


def module(name: str, **attributes) -> ModuleType:
    value = ModuleType(name)
    value.__dict__.update(attributes)
    return value


def load_image_module():
    """Stub the HA boundary while loading the actual image and constants code."""
    package = "_dots_ha_animation_under_test"
    directory = Path(__file__).resolve().parents[1] / "custom_components" / "dots_on_paper"

    def track(hass, callback, interval, **_kwargs):
        timer = Timer(callback, interval)
        hass.timers.append(timer)

        def cancel() -> None:
            timer.active = False

        return cancel

    modules = {
        package: module(package, __path__=[str(directory)]),
        f"{package}.api": module(f"{package}.api", BridgeError=BridgeError),
        f"{package}.coordinator": module(f"{package}.coordinator", DotsCoordinator=object),
        f"{package}.entity": module(f"{package}.entity", DotsEntity=Entity),
        "homeassistant": module("homeassistant", __path__=[]),
        "homeassistant.components": module("homeassistant.components", __path__=[]),
        "homeassistant.components.image": module("homeassistant.components.image", ImageEntity=ImageEntity),
        "homeassistant.config_entries": module("homeassistant.config_entries", ConfigEntry=object),
        "homeassistant.const": module("homeassistant.const", Platform=SimpleNamespace(IMAGE="image", SENSOR="sensor", SELECT="select")),
        "homeassistant.core": module("homeassistant.core", HomeAssistant=object, callback=lambda fn: fn),
        "homeassistant.helpers": module("homeassistant.helpers", __path__=[]),
        "homeassistant.helpers.entity_platform": module("homeassistant.helpers.entity_platform", AddEntitiesCallback=object),
        "homeassistant.helpers.event": module("homeassistant.helpers.event", async_track_time_interval=track),
        "homeassistant.util": module("homeassistant.util", dt=SimpleNamespace(utcnow=lambda: datetime.now(timezone.utc))),
    }
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location(f"{package}.image", directory / "image.py")
        loaded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded)
    return loaded


class HomeAssistantAnimationTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.image_module = load_image_module()

    async def asyncSetUp(self) -> None:
        self.hass = SimpleNamespace(timers=[])
        self.bridge = Bridge()
        self.coordinator = SimpleNamespace(
            data={"revision": 1, "status": "thinking"},
            entry=SimpleNamespace(data={"profile": "oep_400"}, options={"frame_interval": 30}),
            bridge=self.bridge,
            last_update_success=True,
        )
        self.entity = self.image_module.DotsImage(self.hass, self.coordinator)
        await self.entity.async_added_to_hass()

    async def asyncTearDown(self) -> None:
        await self.entity.async_will_remove_from_hass()

    def tick(self) -> None:
        for timer in list(self.hass.timers):
            if timer.active:
                timer.callback(datetime.now(timezone.utc))

    async def test_thinking_advances_without_a_new_revision_and_uses_configured_interval(self) -> None:
        self.assertEqual(self.hass.timers[0].interval.total_seconds(), 30)
        first = await self.entity.async_image()
        self.assertEqual(await self.entity.async_image(), first)
        self.assertEqual(len(self.bridge.calls), 1)
        self.tick()
        self.assertEqual(self.coordinator.data["revision"], 1)
        self.assertEqual(await self.entity.async_image(), b"image-1")
        self.assertEqual(self.bridge.calls, [("oep_400", 0), ("oep_400", 1)])
        self.assertEqual(self.entity.writes, 1)

    async def test_completed_answer_cancels_timer_and_remains_cached(self) -> None:
        await self.entity.async_image()
        self.coordinator.data = {"revision": 2, "status": "answer"}
        self.entity._handle_coordinator_update()
        self.assertFalse(self.hass.timers[0].active)
        self.assertEqual(await self.entity.async_image(), b"image-11")
        for _ in range(15):
            self.tick()
            self.assertEqual(await self.entity.async_image(), b"image-11")
        self.assertEqual(self.bridge.calls, [("oep_400", 0), ("oep_400", 11)])

    async def test_loop_wraps_and_next_run_starts_at_zero(self) -> None:
        for _ in range(12):
            self.tick()
        self.assertEqual(await self.entity.async_image(), b"image-0")
        self.coordinator.data = {"revision": 2, "status": "answer"}
        self.entity._handle_coordinator_update()
        self.coordinator.data = {"revision": 3, "status": "thinking"}
        self.entity._handle_coordinator_update()
        self.assertEqual(sum(timer.active for timer in self.hass.timers), 1)
        self.assertEqual(await self.entity.async_image(), b"image-0")
        self.tick()
        self.assertEqual(await self.entity.async_image(), b"image-1")

    async def test_answer_discards_an_inflight_thinking_image(self) -> None:
        self.bridge.release = asyncio.Event()
        pending = asyncio.create_task(self.entity.async_image())
        await self.bridge.started.wait()
        self.coordinator.data = {"revision": 2, "status": "answer"}
        self.entity._handle_coordinator_update()
        self.bridge.release.set()
        self.assertIsNone(await pending)
        self.assertEqual(await self.entity.async_image(), b"image-11")

    async def test_concurrent_requests_share_one_fetch(self) -> None:
        self.bridge.release = asyncio.Event()
        pending = [asyncio.create_task(self.entity.async_image()) for _ in range(3)]
        await self.bridge.started.wait()
        self.bridge.release.set()
        self.assertEqual(await asyncio.gather(*pending), [b"image-0"] * 3)
        self.assertEqual(len(self.bridge.calls), 1)

    async def test_slow_thinking_fetch_finishes_before_the_next_frame(self) -> None:
        self.bridge.release = asyncio.Event()
        pending = asyncio.create_task(self.entity.async_image())
        await self.bridge.started.wait()
        for _ in range(4):
            self.tick()
        self.assertEqual(self.entity._frame, 0)
        self.assertEqual(self.entity.writes, 0)
        self.bridge.release.set()
        self.assertEqual(await pending, b"image-0")
        self.tick()
        self.assertEqual(await self.entity.async_image(), b"image-1")

    async def test_unavailable_and_unloaded_entities_stop_animation(self) -> None:
        self.coordinator.last_update_success = False
        self.entity._handle_coordinator_update()
        self.assertFalse(self.hass.timers[0].active)
        self.coordinator.last_update_success = True
        self.entity._handle_coordinator_update()
        self.assertTrue(self.hass.timers[-1].active)
        await self.entity.async_will_remove_from_hass()
        self.assertFalse(any(timer.active for timer in self.hass.timers))

    async def test_failed_fetch_retries_without_caching(self) -> None:
        self.bridge.fail = True
        self.assertIsNone(await self.entity.async_image())
        self.bridge.fail = False
        self.assertEqual(await self.entity.async_image(), b"image-0")
        self.assertEqual(len(self.bridge.calls), 2)

    async def test_already_queued_tick_is_harmless_after_removal(self) -> None:
        callback = self.hass.timers[0].callback
        await self.entity.async_will_remove_from_hass()
        callback(datetime.now(timezone.utc))
        self.assertEqual(self.entity.writes, 0)
        self.assertEqual(self.entity._frame, 0)


if __name__ == "__main__":
    unittest.main()
