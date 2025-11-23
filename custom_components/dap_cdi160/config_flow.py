"""Config flow for DAP CDI160-BT Audio Player integration."""
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_NAME, DOMAIN, ENDPOINT_GET_PLAYING

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
