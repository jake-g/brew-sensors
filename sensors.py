import logging
from datetime import datetime

import Adafruit_MCP9808.MCP9808 as MCP9808
import forecastio
from pytz import timezone

from tilt import get_tilt


def c_to_f(c):
    return c * 9.0 / 5.0 + 32.0


class Sensor:
    def get_reading(self):
        return {}  # TODO enforce this is a dict

    def get_col_name(self):
        return ''


class Timestamp(Sensor):
    def __init__(self, timezone='UTC', format='%m-%d-%Y %H:%M'):
        self.__dict__.update(locals())

    def get_reading(self):
        return {'time': datetime.now(timezone(self.timezone)).strftime(self.format)}

    def get_col_name(self):
        return ''


class Forcast(Sensor):
    def __init__(self, api_key, lat, lng):
        self.__dict__.update(locals())

    def get_reading(self):

        try:
            darksky_forcast = forecastio.load_forecast(self.api_key, self.lat, self.lng).currently()
            return darksky_forcast.__dict__
            # darksky_temp = float(darksky_forcast.temperature)
        except Exception as e:
            logging.error('Failed to get DarkSky data...\n%s' % e)


class TiltHydrometer(Sensor):
    def __init__(self, color, use_celcius=False):
        self.__dict__.update(locals())

    def get_reading(self):
        try:
            tilt_reading = get_tilt(self.color)
            return {
                'temperature': float(tilt_reading.get_temp(celcius=self.use_celcius)),
                'gravity': float(tilt_reading.get_gravity())
                'temperature_unit': 'C' if self.use_celcius else 'F'
            }
        except Exception as e:
            logging.error('Failed to get DarkSky data...\n%s' % e)


class TemperatureMCP9808(Sensor):
    def __init__(self, use_celcius=False):
        self._sensor = None
        self.__dict__.update(locals())
        self._init_sensor()

    def _init_sensor(self):
        try:  # Default constructor will use the default I2C address (0x18) and pick a default I2C bus.
            self._sensor = MCP9808.MCP9808()
            self._sensor.begin()
        except Exception as e:
            logging.error('Failed to initialize MCP9808 ambient temp sensor...\n%s' % e)

    def get_reading(self):
        try:
            ambient_temp = float(self._sensor.readTempC())
            if not self.use_celcius:
                ambient_temp = c_to_f(ambient_temp)
            return {
                'temperature': ambient_temp,
                'temperature_unit': 'C' if self.use_celcius else 'F'
            }
        except Exception as e:
            logging.error('Failed to get MCP9808 ambient temp sensor data...\n%s' % e)
