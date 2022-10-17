"""
Module for FVM controller.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Final, List

from homeassistant.helpers.typing import HomeAssistantType

from custom_components.fvm.const import DATA_CONTROLLER, DOMAIN
from custom_components.fvm.fvm_session import FvmCustomerServiceSession


@dataclass
class ReadingTime:
    """
    Represents a meter reading time.

    Attributes:
        start: The start date of the reading.
        end: The end date of the reading.
        mode: The reading mode.
    """

    # pylint: disable=invalid-name
    start: Final[datetime]
    # pylint: disable=invalid-name
    end: Final[datetime]
    # pylint: disable=invalid-name
    mode: Final[str]

    def __repr__(self) -> str:
        """Returns the string representation of the class."""
        return f"{self.start}-{self.end}: {self.mode}"


@dataclass
class LocationAndMeter:
    """
    Represents a location with a meter.

    Attributes:
        location_name: The name (address) of the location.
        location_id: The location id. The value of this id is uncertain.
        meter_serial_number: The meter's serial number.
    """

    # pylint: disable=invalid-name
    location_id: Final[str]
    # pylint: disable=invalid-name
    meter_serial_number: Final[str]
    # pylint: disable=invalid-name
    location_name: Final[str]


class FvmController:
    """
    Represents a controller class for FVM.
    """

    def __init__(self, username: str, password: str):
        """
        Initialize a new instance of FvmController class.

        Args:
            username: The registered username (email address).
            password: The password for the user.
        """
        self._username = username
        self._password = password

    async def get_locations_and_meters(self) -> List[LocationAndMeter]:
        """
        Gets the registered locations and meters for the user.

        Returns:
            The registered locations and meters for the user.
        """
        async with FvmCustomerServiceSession() as session:
            await session.get_root_page()
            if await session.post_login(self._username, self._password):
                locations = await session.get_locations_and_serial_numbers()
                return [
                    LocationAndMeter(
                        location["FOGYH_MN"], location["ANLAGE"], location["SERGE"]
                    )
                    for location in locations["FogyHely"]["T_FOGYH"]
                ]

    async def get_dictation_and_reading_times(
        self, location_id: str, meter_serial_number: str
    ) -> List[ReadingTime]:
        """
        Gets the dictation and reading times for the specified meter.

        Args:
            location_id: The location id.
            meter_serial_number: The meter's serial number.

        Returns:
            The reading times for the specified meter.
        """
        async with FvmCustomerServiceSession() as session:
            await session.get_root_page()
            if await session.post_login(self._username, self._password):
                reading_data = await session.get_dictation_and_reading_times(
                    location_id, meter_serial_number
                )

                return sorted(
                    [
                        ReadingTime(
                            datetime.strptime(reading["LEOIDOSZAK"][:10], "%Y.%m.%d"),
                            datetime.strptime(reading["LEOIDOSZAK"][11:22], "%Y.%m.%d"),
                            reading["LEOMOD"],
                        )
                        for reading in reading_data["DataModel"]["LeolvDiktIdoszakok"]
                    ],
                    key=lambda reading: reading.start,
                )


def set_controller(
    hass: HomeAssistantType, user_name: str, controller: FvmController
) -> None:
    """
    Sets the controller instance for the specified username in Home Assistant data container.

    Args:
        hass: The Home Assistant instance.
        user_name: The registered username.
        controller: The controller instance to set.
    """
    hass.data[DOMAIN][DATA_CONTROLLER][user_name] = controller


def get_controller(hass: HomeAssistantType, user_name: str) -> FvmController:
    """
    Gets the controller instance for the specified username from Home Assistant data container.

    Args:
        hass: The Home Assistant instance.
        user_name: The registered username.

    Returns:
        The controller associated to the specified username.
    """
    return hass.data[DOMAIN][DATA_CONTROLLER].get(user_name)


def is_controller_exists(hass: HomeAssistantType, user_name: str) -> bool:
    """
    Gets the value indicates whether a controller associated to the specified
    username in Home Assistant data container.

    Args:
        hass: The Home Assistant instance.
        user_name: The registered username.

    Returns:
        The value indicates whether a controller associated to the specified
        username in Home Assistant data container.
    """
    return user_name in hass.data[DOMAIN][DATA_CONTROLLER]
