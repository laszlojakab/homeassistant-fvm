# pylint: disable=bad-continuation
"""
The configuration flow module for FVM integration.
"""
from typing import Any, Dict

import voluptuous as vol
from homeassistant.config_entries import HANDLERS, ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .fvm_session import FvmCustomerServiceSession


class FvmOptionsFlowHandler(OptionsFlow):
    """Handle FVM options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """
        Initialize a new instance of FvmOptionsFlowHandler class.

        Args:
            config_entry: The config entry of the integration.
        """
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Dict[str, Any] = None) -> FlowResult:
        """
        Handles FVM configuration init step.

        Args:
            user_input:
                The dictionary contains the settings entered by the user
                on the configuration screen.
        Returns
            The flow result of the step.
        """
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_PASSWORD, default=self.config_entry.data[CONF_PASSWORD]
                ): str
            }
        )

        if user_input is not None:
            async with FvmCustomerServiceSession() as session:
                if not await session.post_login(
                    self.config_entry.data[CONF_USERNAME], user_input[CONF_PASSWORD]
                ):
                    return self.async_show_form(
                        step_id="init",
                        data_schema=data_schema,
                        errors={"base": "invalid_username_or_password"},
                    )

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=self.config_entry.data | user_input
            )

            return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(step_id="init", data_schema=data_schema)


@HANDLERS.register(DOMAIN)
class FvmConfigFlow(ConfigFlow, domain=DOMAIN):
    """
    Configuration flow handler for Fvm integration.
    """

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigFlow) -> FvmOptionsFlowHandler:
        """
        Gets the options flow handler for the integration.

        Args:
            config_entry: The config entry of the integration.

        Returns: The options flow handler for the integration.
        """
        return FvmOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: Dict[str, Any]) -> FlowResult:
        """
        Handles the step when integration added from the UI.

        Args:
            user_input: The inputs filled by the user. 
            It is `None` when the user enters to the step first time.
        """
        data_schema = vol.Schema(
            {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
        )

        if user_input is not None:
            async with FvmCustomerServiceSession() as session:
                if not await session.post_login(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                ):
                    return self.async_show_form(
                        step_id="user",
                        data_schema=data_schema,
                        errors={CONF_USERNAME: "invalid_username_or_password"},
                    )

            await self.async_set_unique_id(user_input[CONF_USERNAME])
            self._abort_if_unique_id_configured()

            data = {
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }

            return self.async_create_entry(
                title=f"Fővárosi Vízművek ({user_input[CONF_USERNAME]})", data=data
            )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )
