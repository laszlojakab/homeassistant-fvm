'''
Module for FVM integration.
'''

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .const import DATA_CONTROLLER, DOMAIN
from .fvm_controller import (FvmController,
                             is_controller_exists, set_controller)


# pylint: disable=unused-argument
async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
    '''
    Set up the FVM component.

    Parameters
    ----------
    hass: homeassistant.helpers.typing.HomeAssistantType
        The Home Assistant instance.
    config: homeassistant.helpers.typing.ConfigType
        The configuration.

    Returns
    -------
    bool
        The value indicates whether the setup succeeded.
    '''
    hass.data[DOMAIN] = {DATA_CONTROLLER: {}}
    return True


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry) -> bool:
    '''
    Initialize the sensors based on the config entry.

    Parameters
    ----------
    hass: homeassistant.helpers.typing.HomeAssistantType
        The Home Assistant instance.
    config_entry: homeassistant.config_entries.ConfigEntry
        The config entry which contains information gathered by the config flow.

    Returns
    -------
    bool
        The value indicates whether the setup succeeded.
    '''

    if not is_controller_exists(hass, config_entry.data[CONF_USERNAME]):
        set_controller(
            hass,
            config_entry.data[CONF_USERNAME],
            FvmController(
                config_entry.data[CONF_USERNAME],
                config_entry.data[CONF_PASSWORD]
            )
        )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "calendar")
    )

    return True
