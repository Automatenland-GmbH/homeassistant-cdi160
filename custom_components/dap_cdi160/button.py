"""Button platform for DAP CDI160-BT Audio Player."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DAP CDI160 button entities."""
    host = config_entry.data[CONF_HOST]
    name = config_entry.data.get(CONF_NAME, DEFAULT_NAME)

    async_add_entities([RefreshPresetInfoButton(hass, config_entry, host, name)])


class RefreshPresetInfoButton(ButtonEntity):
    """Button to refresh preset information from device."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        host: str,
        name: str,
    ) -> None:
        """Initialize the button."""
        self.hass = hass
        self._config_entry = config_entry
        self._host = host
        self._device_name = name
        self._attr_unique_id = f"dap_cdi160_{host}_refresh_presets"
        self._attr_name = "Refresh preset info"

    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": self._device_name,
            "manufacturer": "DAP",
            "model": "CDI160-BT",
        }

    async def async_press(self) -> None:
        """Handle the button press - refresh preset info."""
        _LOGGER.info("Refreshing preset info for %s", self._host)

        # Find the media player entity
        for entity in self.hass.data.get("entity_components", {}).get("media_player", {}).entities:
            if hasattr(entity, "_host") and entity._host == self._host:
                _LOGGER.info("Found media player entity, refreshing preset info")
                await entity.async_refresh_preset_info()
                _LOGGER.info("Preset info refreshed successfully")
                return

        _LOGGER.warning("Could not find media player entity to refresh")
