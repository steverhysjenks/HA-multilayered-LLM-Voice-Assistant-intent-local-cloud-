"""Config flow for Jarvis Router."""

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, CONF_URL, DOMAIN


class JarvisRouterConfigFlow(
    ConfigFlow,
    domain=DOMAIN,
):
    """Configure Jarvis Router."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle initial setup."""

        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            api_key = user_input[CONF_API_KEY]

            # /health does not require the bearer token. This only proves
            # network reachability and that the expected service is alive.
            try:
                session = async_get_clientsession(self.hass)

                async with session.get(
                    f"{url}/health",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status != 200:
                        errors["base"] = "cannot_connect"

            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                # One Jarvis Router entry is sufficient for this design.
                await self.async_set_unique_id("jarvis_router")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Jarvis Router",
                    data={
                        CONF_URL: url,
                        CONF_API_KEY: api_key,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL,
                        default="http://192.168.0.121:8099",
                    ): str,
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )
