"""Platform for sensor integration."""
from datetime import timedelta
import logging
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_point_in_time
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    try:
        today_sensor = ChineseCalendarSensor(hass)
        async_track_point_in_time(
            hass, today_sensor.point_in_time_listener, today_sensor.get_next_interval()
        )
        
        tomorrow_sensor = TomorrowChineseCalendarSensor(hass)
        async_track_point_in_time(
            hass, tomorrow_sensor.point_in_time_listener, tomorrow_sensor.get_next_interval()
        )
        
        async_add_entities([today_sensor, tomorrow_sensor], True)
    except ImportError as err:
        _LOGGER.error("Error importing chinese_calendar: %s", err)
        return False

class ChineseCalendarSensor(Entity):
    """Representation of Chinese Calendar Sensor."""
    def __init__(self, hass):
        """Initialize the sensor."""
        self._attr_name = "Chinese Calendar"
        self._attr_icon = "mdi:calendar"
        self._attr_should_poll = False
        self._attr_unique_id = "chinese_calendar_sensor"
        self.hass = hass
        self._last_update_date = None
        self._data = {}
        self.update_internal_state()

    @property
    def state(self):
        """Return the state of the sensor."""
        return "workday" if self._data.get("is_workday") else "holiday"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._data

    def update_internal_state(self):
        """Update the internal state."""
        now = dt_util.now()
        # Only update if date has changed to avoid unnecessary updates
        if now.date() == self._last_update_date:
            return

        try:
            from chinese_calendar import is_workday, get_holiday_detail, is_in_lieu
            on_holiday, holiday_name = get_holiday_detail(now)
            self._data = {
                "is_workday": is_workday(now),
                "is_holiday": on_holiday,
                "holiday_name": holiday_name,
                "is_in_lieu": is_in_lieu(now),
                "last_updated": now.isoformat(),
                "date": now.date().isoformat(),
            }
            self._last_update_date = now.date()
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Error updating Chinese calendar: %s", err)
            self._data["error"] = str(err)

    def get_next_interval(self):
        """Return next update interval."""
        return dt_util.start_of_local_day(dt_util.now() + timedelta(days=1))

    @callback
    def point_in_time_listener(self, _now=None):
        """Callback for scheduled updates."""
        self.update_internal_state()
        self.async_write_ha_state()
        async_track_point_in_time(
            self.hass, self.point_in_time_listener, self.get_next_interval()
        )

class TomorrowChineseCalendarSensor(ChineseCalendarSensor):
    """Representation of Tomorrow's Chinese Calendar Sensor."""
    
    def __init__(self, hass):
        """Initialize the sensor."""
        super().__init__(hass)
        self._attr_name = "Tomorrow Chinese Calendar"
        self._attr_unique_id = "tomorrow_chinese_calendar_sensor"
    
    def update_internal_state(self):
        """Update the internal state for tomorrow's date."""
        now = dt_util.now()
        tomorrow = now + timedelta(days=1)
        
        if tomorrow.date() == self._last_update_date:
            return
            
        try:
            from chinese_calendar import is_workday, get_holiday_detail, is_in_lieu
            on_holiday, holiday_name = get_holiday_detail(tomorrow)
            self._data = {
                "is_workday": is_workday(tomorrow),
                "is_holiday": on_holiday,
                "holiday_name": holiday_name,
                "is_in_lieu": is_in_lieu(tomorrow),
                "last_updated": now.isoformat(),
                "date": tomorrow.date().isoformat(),
            }
            self._last_update_date = tomorrow.date()
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Error updating Tomorrow Chinese calendar: %s", err)
            self._data["error"] = str(err)
