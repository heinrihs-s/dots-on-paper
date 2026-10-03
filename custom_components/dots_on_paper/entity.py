"""Common entity identity for each configured bridge."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DotsCoordinator


class DotsEntity(CoordinatorEntity[DotsCoordinator]):
    """Attach bridge entities without exposing credentials."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DotsCoordinator, key: str) -> None:
        super().__init__(coordinator)
        identity = f"{coordinator.bridge_id}_{coordinator.entry.entry_id}"
        self._attr_unique_id = f"{identity}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identity)},
            name=coordinator.entry.title,
            manufacturer="Dots on Paper",
            model="Local e-ink bridge",
        )
