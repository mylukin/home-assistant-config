import logging
from datetime import timedelta

import voluptuous as vol
import requests

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    TEMP_CELSIUS, CONF_MONITORED_CONDITIONS, CONF_NAME, STATE_UNKNOWN,
    ATTR_ATTRIBUTION)
from homeassistant.helpers.entity import Entity

REQUIREMENTS = ['pyquery==1.4.0', 'requests==2.20.1']

_LOGGER = logging.getLogger(__name__)

DOMAIN = "moji_weather"

CONF_ATTRIBUTION = "墨迹天气"

DEFAULT_NAME = 'Moji Weather'

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=10)

SENSOR_TYPES = {
    'weather_current': ['Current', None],
    'weather': ['Condition', None],
    'weather_tips': ['Tips', None],
    'temperature': ['Temperature', 'temperature'],
    'temp_min': ['Temperature min', 'temperature'],
    'temp_max': ['Temperature max', 'temperature'],
    'wind_grade': ['Wind Grade', None],
    'air_quality': ['Air Quality', None],
    'humidity': ['Humidity', '%'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_MONITORED_CONDITIONS, default=[]):
        [vol.In(SENSOR_TYPES)],
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    unit = hass.config.units.temperature_unit
    name = config.get(CONF_NAME)

    SENSOR_TYPES['temperature'][1] = unit
    SENSOR_TYPES['temp_min'][1] = unit
    SENSOR_TYPES['temp_max'][1] = unit

    dev = []
    for variable in config[CONF_MONITORED_CONDITIONS]:
        dev.append(MojiWeatherSensor(name, variable))

    add_devices(dev, True)


class MojiWeatherSensor(Entity):
    """Implementation of the Yahoo! weather sensor."""

    def __init__(self, name, sensor_type):
        """Initialize the sensor."""
        self._client = name
        self._name = SENSOR_TYPES[sensor_type][0]
        self._type = sensor_type
        self._state = STATE_UNKNOWN
        self._unit = SENSOR_TYPES[sensor_type][1]
        self._code = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format(self._client, self._name)

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    @property
    def entity_picture(self):
        """Return the entity picture to use in the frontend, if any."""
        if self._code is None or "weather" not in self._type:
            return None

        return self._code

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
        }

    def update(self):
        """Get the latest data from Yahoo! and updates the states."""
        # 获取墨迹天气的数据
        tianqi_url = "http://tianqi.moji.com/weather/china/shanghai/pudong-new-district"
        _LOGGER.info("URL: {}".format(tianqi_url))
        try:
            resp = requests.get(tianqi_url, timeout=10)
            if resp.status_code == 200:
                import re
                from pyquery import PyQuery as pq
                d = pq(resp.text)

                # Default code for weather image
                self._code = d('.wea_weather span img').attr('src')

                # Read data
                if self._type == 'weather_current':
                    self._code = d('.wea_weather img').attr('src')
                    self._state = d('.wea_weather b').text()
                elif self._type == 'weather':
                    self._code = d('.forecast ul.days:eq(0) li:eq(1) img').attr('src')
                    self._state = d('.forecast ul.days:eq(0) li:eq(1)').text()
                elif self._type == 'weather_tips':
                    self._state = d('.wea_tips em').text()
                elif self._type == 'temperature':
                    self._state = d('.wea_weather em').text()
                elif self._type == 'temp_min':
                    self._state = d('.forecast ul.days:eq(0) li:eq(2)').text().split('/')[0].replace('°', '').strip()
                elif self._type == 'temp_max':
                    self._state = d('.forecast ul.days:eq(0) li:eq(2)').text().split('/')[1].replace('°', '').strip()
                elif self._type == 'wind_grade':
                    self._state = re.sub(r'[^\d]', '', d('.wea_about em').text())
                elif self._type == 'air_quality':
                    self._code = d('.wea_alert img').attr('src')
                    self._state = re.sub(r'[^\d]', '', d('.wea_alert em').text())
                elif self._type == 'humidity':
                    self._state = re.sub(r'[^\d]', '', d('.wea_about span').text())

        except Exception as e:
            _LOGGER.error("Request URL Error: {}".format(e))
            _LOGGER.error("Request Timeout URL: {}".format(tianqi_url))
