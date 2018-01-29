import logging
import RPi.GPIO as GPIO
from datetime import timedelta

import voluptuous as vol
import requests

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    TEMP_CELSIUS, CONF_MONITORED_CONDITIONS, CONF_NAME, STATE_UNKNOWN,
    ATTR_ATTRIBUTION)
from homeassistant.helpers.entity import Entity

REQUIREMENTS = ['RPi.GPIO==0.6.3']

_LOGGER = logging.getLogger(__name__)

DOMAIN = "anyone_there"

CONF_ATTRIBUTION = "是否有人"

DEFAULT_NAME = 'Anyone There'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    name = config.get(CONF_NAME)

    add_devices([AnyoneThereSensor(name)], True)


class AnyoneThereSensor(Entity):
    """Implementation of the Yahoo! weather sensor."""

    def __init__(self, name):
        """Initialize the sensor."""
        self._name = name
        self._state = STATE_UNKNOWN

        GPIO.setmode(GPIO.BCM)

        self.PIR_PIN = 21

        GPIO.setup(self.PIR_PIN, GPIO.IN)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
        }

    def update(self):
        """Get the latest data from Yahoo! and updates the states."""

        if GPIO.input(self.PIR_PIN):
            self._state = 'yes'
        else:
            self._state = 'no'
