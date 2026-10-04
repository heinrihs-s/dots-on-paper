"""Choose the character and how replies appear on the display."""

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import BridgeError
from .const import CHARACTERS, DISPLAY_MODES
from .coordinator import DotsCoordinator
from .entity import DotsEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([DotsCharacter(entry.runtime_data), DotsDisplayMode(entry.runtime_data)])


class DotsCharacter(DotsEntity, SelectEntity):
    _attr_name = "Character"
    _attr_icon = "mdi:palette-outline"
    _attr_options = list(CHARACTERS)

    def __init__(self, coordinator: DotsCoordinator) -> None:
        super().__init__(coordinator, "character")

    @property
    def current_option(self) -> str:
        return self.coordinator.data["character"]

    async def async_select_option(self, option: str) -> None:
        if option not in CHARACTERS:
            raise HomeAssistantError("Unknown dot character")
        if option == self.current_option:
            return
        try:
            await self.coordinator.set_character(option)
        except BridgeError as err:
            raise HomeAssistantError(str(err)) from err


class DotsDisplayMode(DotsEntity, SelectEntity):
    _attr_translation_key = "display_mode"
    _attr_icon = "mdi:message-text-outline"
    _attr_options = list(DISPLAY_MODES)

    def __init__(self, coordinator: DotsCoordinator) -> None:
        super().__init__(coordinator, "display_mode")

    @property
    def current_option(self) -> str:
        return self.coordinator.data.get("mode", "last_reply")

    async def async_select_option(self, option: str) -> None:
        if option not in DISPLAY_MODES:
            raise HomeAssistantError("Unknown display mode")
        if option == self.current_option:
            return
        try:
            await self.coordinator.set_mode(option)
        except BridgeError as err:
            raise HomeAssistantError(str(err)) from err
