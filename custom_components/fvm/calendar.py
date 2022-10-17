"""
The calendar module for FVM integration.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from dateutil import tz
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.util import Throttle

from custom_components.fvm.fvm_controller import (FvmController,
                                                  LocationAndMeter,
                                                  ReadingTime, get_controller)

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(days=7)


class FvmReadingTimeCalendarEventDevice(CalendarEntity):
    """
    Represents the FVM reading time calendar event device.
    """

    def __init__(
        self, config_entry_id: str, controller: FvmController, meter: LocationAndMeter
    ):
        """
        Initialize a new instance of FvmReadingTimeCalendarEventDevice class.

        Args:
            config_entry_id: The config_entry.entry_id which created the instance.
            controller: The FVM controller instance.
            meter:The location and meter information.
        """
        self._controller = controller
        self._meter = meter
        self._attr_name = (
            f"fvm_{meter.location_id}_{meter.meter_serial_number}_dictation_and_reading"
        )
        self._attr_unique_id = (
            f"{config_entry_id}_{meter.location_id}"
            "_{meter.meter_serial_number}_dictation_and_reading"
        )
        self._dictation_and_reading_times: List[ReadingTime] = []
        self._event: CalendarEvent | None = None
        self._all_events = []

    @property
    def event(self) -> Dict[str, Any]:
        """
        Gets the next upcoming reading event.
        """
        return self._event

    async def async_update(self):
        """
        Updates the next event in the calendar.
        """
        await self._update_dictation_and_reading_times()
        if len(self._dictation_and_reading_times) == 0:
            self._event = None
        else:
            self._event = self._get_event(self._dictation_and_reading_times[0])

    async def async_get_events(
        self, hass: HomeAssistantType, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """
        Return calendar events within a datetime range.

        Args:
            hass: The Home Assistant instance.
            start_date: The datetime range start.
            end_date: The datetime range end.
        """
        await self._update_dictation_and_reading_times()
        local_zone = tz.tzlocal()
        start_date = start_date.astimezone(local_zone).replace(tzinfo=None)
        end_date = end_date.astimezone(local_zone).replace(tzinfo=None)

        result: List[CalendarEvent] = []
        for reading_time in self._dictation_and_reading_times:
            latest_start = max(start_date, reading_time.start)
            earliest_end = min(end_date, reading_time.end)
            delta = (earliest_end - latest_start).days + 1
            overlap = delta > 0
            if overlap:
                result.append(self._get_event(reading_time))
        return result

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def _update_dictation_and_reading_times(self):
        self._dictation_and_reading_times = [
            reading_time
            for reading_time in await self._controller.get_dictation_and_reading_times(
                self._meter.location_id, self._meter.meter_serial_number
            )
            if reading_time.end >= datetime.today()
        ]

    @classmethod
    def _get_event(cls, reading_time: ReadingTime) -> Dict[str, Any]:
        return CalendarEvent(
            start=reading_time.start.date(),
            end=reading_time.end.date(),
            summary=f"Fővárosi vízművek - {reading_time.mode}",
            description=reading_time.mode,
            location="https://ugyfelszolgalat.vizmuvek.hu/",
        )


async def async_setup_entry(
    hass: HomeAssistantType,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """
    Setup of FVM calendars for the specified config_entry.

    Args:
        hass: The Home Assistant instance.
        config_entry:  The config entry which is used to create sensors.
        async_add_entities:  The callback which can be used to add new entities to Home Assistant.

    Returns:
        The value indicates whether the setup succeeded.
    """

    _LOGGER.info("Setting up FVM calendar events.")

    controller = get_controller(hass, config_entry.data[CONF_USERNAME])

    async_add_entities(
        [
            FvmReadingTimeCalendarEventDevice(config_entry.entry_id, controller, meter)
            for meter in await controller.get_locations_and_meters()
        ]
    )

    _LOGGER.info("Setting up FVM calendar events completed.")
