import logging
from datetime import datetime

import forecastio
from pytz import timezone

import board
import adafruit_ina219
import adafruit_bh1750
import adafruit_veml6070
import adafruit_mcp9808

class Timestamp:
    def __init__(self, timezone="US/Pacific" , format="%m-%d-%Y %H:%M"):
        self.timezone=timezone
        self.format=format

    def get_reading(self):
        return {"time": datetime.now(timezone(self.timezone)).strftime(self.format)}


class Forcast:
    def __init__(self, api_key, lat, lng):
        self.lat = lat
        self.lng = lng
        self.api_key = api_key
        self.last_reading = None

    def get_reading(self):
        try:
            darksky_forcast = forecastio.load_forecast(
                self.api_key, self.lat, self.lng
            ).currently()
            return darksky_forcast.d
        except Exception as e:
            logging.error("Failed to get DarkSky data...\n  %s" % e)


class HighSideCurrentINA219:
    def __init__(self, address=0x44):
        self._sensor = None
        self.address = address
        self.model = "INA219"
        self.url = "https://learn.adafruit.com/adafruit-ina219-current-sensor-breakout/"
        self._init_sensor()

    def _init_sensor(self):
        try:
            if self.address:
                self._sensor = adafruit_ina219.INA219(board.I2C(), addr=self.address)
            else:
                self._sensor = adafruit_ina219.INA219(board.I2C())
        except Exception as e:
            logging.error(
                "Failed to initialize %s current sensor...\n  %s" % (self.model, e)
            )

    def get_reading(self):
        try:
            return {
                "load_voltage": round(
                    self._sensor.bus_voltage, 6
                ),  # voltage on V- (load side)
                "shunt_voltage": round(
                    self._sensor.shunt_voltage, 6
                ),  # voltage between V+ and V- across the shunt
                "load_current": round(self._sensor.current, 6),  # current in mA
            }
        except Exception as e:
            logging.error(
                "Failed to get %s current sensor data...\n  %s" % (self.model, e)
            )


class TemperatureMCP9808:
    def __init__(self, use_celcius=False, address=0x18):
        self._sensor = None
        self.address = address
        self.use_celcius = use_celcius
        self.model = "MCP9808"
        self.url = "https://learn.adafruit.com/adafruit-mcp9808-precision-i2c-temperature-sensor-guide/"
        self._init_sensor()

    def _init_sensor(self):
        try:
            self._sensor = adafruit_mcp9808.MCP9808(board.I2C())
        except Exception as e:
            logging.error(
                "Failed to initialize %s ambient temp sensor...\n  %s" % (self.model, e)
            )

    def c_to_f(self, c):
        return c * 9.0 / 5.0 + 32.0

    def get_reading(self):
        try:
            ambient_temp = self._sensor.temperature
            if not self.use_celcius:
                ambient_temp = self.c_to_f(ambient_temp)
            return {
                "temperature": ambient_temp,
            }
        except Exception as e:
            logging.error(
                "Failed to get %s ambient temp sensor data...\n  %s" % (self.model, e)
            )


class AmbientLightBH1750:
    def __init__(self, address=0x23):
        self._sensor = None
        self.address = address
        self.model = "BH1750"
        self.url = "https://learn.adafruit.com/adafruit-bh1750-ambient-light-sensor"
        self._init_sensor()

    def _init_sensor(self):
        try:
            self._sensor = adafruit_bh1750.BH1750(board.I2C())
        except Exception as e:
            logging.error(
                "Failed to initialize %s lux sensor...\n  %s" % (self.model, e)
            )

    def get_reading(self):
        try:
            return {"lux": round(self._sensor.lux, 6)}
        except Exception as e:
            logging.error("Failed to get %s lux sensor data...\n  %s" % (self.model, e))


class UvVEML6070:
    def __init__(self, address=0x18):
        self._sensor = None
        self.address = address
        self.model = "VEML6070"
        self.url = (
            "https://learn.adafruit.com/adafruit-veml6070-uv-light-sensor-breakout"
        )
        self._init_sensor()

    def _init_sensor(self):
        try:
            self._sensor = adafruit_veml6070.VEML6070(board.I2C())
        except Exception as e:
            logging.error(
                "Failed to initialize %s UV sensor...\n  %s" % (self.model, e)
            )

    def get_reading(self):
        try:
            return {
                "uv": self._sensor.uv_raw,
                "uv_index": self._sensor.get_index(self._sensor.uv_raw),
            }
        except Exception as e:
            logging.error("Failed to get %s UV sensor data...\n  %s" % (self.model, e))

