import logging
from datetime import timedelta
from datetime import datetime

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, STATE_UNKNOWN, ATTR_DATE, ATTR_ATTRIBUTION)
from homeassistant.helpers.entity import Entity

import chinese_calendar as calendar

REQUIREMENTS = ['chinesecalendar==1.0.3']

_LOGGER = logging.getLogger(__name__)

DOMAIN = "chinese_calendar"

CONF_ATTRIBUTION = "中国节假日"

DEFAULT_NAME = 'Chinese Calendar'

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    name = config.get(CONF_NAME)

    add_devices([ChineseCalendarSensor(name)], True)


class ChineseCalendarSensor(Entity):
    """Implementation of the Yahoo! weather sensor."""

    def __init__(self, name):
        """Initialize the sensor."""
        self._name = name
        self._state = STATE_UNKNOWN
        self._attr_name = ''

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def state_attributes(self):
        """Return the state attributes.

        Implemented by component base class.
        """
        return {
            ATTR_DATE: datetime.today().date().strftime('%Y-%m-%d'),
            'name': self._attr_name
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
        }

    def update(self):
        """Get the latest data from Yahoo! and updates the states."""
        is_holiday, holiday_name = calendar.get_holiday_detail(datetime.today().date())
        if is_holiday:
            self._state = 'holiday'
            self._attr_name = holiday_name
        else:
            self._state = 'workday'
