"""Config flow for DAP CDI160-BT Audio Player integration."""
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_NAME, DOMAIN, ENDPOINT_GET_PLAYING, MAX_FAVORITES, MAX_PRESETS

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"

    session = async_get_clientsession(hass)
    url = f"{host}{ENDPOINT_GET_PLAYING}"

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            await response.json()
    except Exception as err:
        _LOGGER.error("Error connecting to DAP CDI160 at %s: %s", url, err)
        raise

    return {"title": data.get(CONF_NAME, DEFAULT_NAME)}


class DapCdi160ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DAP CDI160."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return DapCdi160OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class DapCdi160OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for DAP CDI160."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Build schema for preset and favorite names
        options_schema = {}

        # Add preset name fields
        for i in range(1, MAX_PRESETS + 1):
            key = f"preset_{i}_name"
            default = self.config_entry.options.get(key, f"Preset {i}")
            options_schema[vol.Optional(key, default=default)] = str

        # Add favorite name fields
        for i in range(1, MAX_FAVORITES + 1):
            key = f"favorite_{i}_name"
            default = self.config_entry.options.get(key, f"Favorite {i}")
            options_schema[vol.Optional(key, default=default)] = str

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options_schema),
        )
