import logging
from datetime import datetime
import os
import time
import forecastio
from pytz import timezone

import board
import adafruit_ina219
import adafruit_ina260
import adafruit_bh1750
import adafruit_veml6070
import adafruit_mcp9808
import adafruit_bme280
import adafruit_tsl2591


def celcius_to_fahrenheit(celcius):
    return float(celcius) * 9.0 / 5.0 + 32.0


def fahrenheit_to_celcius(fahrenheit):
    return (float(fahrenheit) - 32.0) * 5.0 / 9.0


class Timestamp:
    def __init__(self, timezone="US/Pacific", format="%m-%d-%Y %H:%M"):
        self.timezone = timezone
        self.format = format

    def get_reading(self):
        return {"time": datetime.now(timezone(self.timezone)).strftime(self.format)}


class Forecast:
    def __init__(self, api_key, lat, lng, use_celcius=False, rate_limit_seconds=180):
        self.lat = lat
        self.lng = lng
        self.api_key = api_key
        self.use_celcius = use_celcius
        self.last_reading = None
        self.last_reading_timestamp = 0
        self.rate_limit_seconds = rate_limit_seconds

    def get_reading(self):
        try:
            last_reading_delta = time.time() - self.last_reading_timestamp
            if last_reading_delta > self.rate_limit_seconds:
                darksky_forecast = forecastio.load_forecast(
                    self.api_key, self.lat, self.lng
                ).currently()
                self.last_reading = darksky_forecast
                self.last_reading_timestamp = time.time()
            else:
                logging.warning(
                    "Last reading was %ds ago which is less than the rate limit period of %ds, reusing last result..." % (last_reading_delta, self.rate_limit_seconds)
                )
                darksky_forecast = self.last_reading
            
            if self.use_celcius:
                darksky_forecast.d["temperature_C"] = fahrenheit_to_celcius(
                    darksky_forecast.d.pop("temperature", None)
                )
            else:
                darksky_forecast.d["temperature_F"] = darksky_forecast.d.pop(
                    "temperature", None
                )
            return darksky_forecast.d
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
                "voltage": self._sensor.bus_voltage,  # voltage on V- (load side)
                "current": self._sensor.current,  # current in mA
                "shunt_voltage": self._sensor.shunt_voltage,  # voltage between V+ and V- across the shunt
            }
        except Exception as e:
            logging.error(
                "Failed to get %s current sensor data...\n  %s" % (self.model, e)
            )

class HighSideCurrentINA260:
    def __init__(self, address=0x44):
        self._sensor = None
        self.address = address
        self.model = "INA260"
        self.url = "https://learn.adafruit.com/adafruit-ina260-current-voltage-power-sensor-breakout/"
        self._init_sensor()

    def _init_sensor(self):
        try:
            if self.address:
                self._sensor = adafruit_ina260.INA260(board.I2C(), address=self.address)
            else:
                self._sensor = adafruit_ina260.INA260(board.I2C())
        except Exception as e:
            logging.error(
                "Failed to initialize %s current sensor...\n  %s" % (self.model, e)
            )

    def get_reading(self):
        try:
            #print('Shunt: %s\t%0.2f V\t%0.2f mA\t%0.2f W'% (hex(self.address), self._sensor.voltage, self._sensor.current, self._sensor.power/1000.0))
            return {
                "voltage": self._sensor.voltage,  # voltage on V- (load side)
                "current": self._sensor.current,  # current in mA
                "power": self._sensor.power,
            }
        except Exception as e:
            logging.error(
                "Failed to get %s current sensor data...\n  %s" % (self.model, e)
            )

class PiSensors:
    # TODO get  Wifi strength
    def __init__(self, use_celcius=False):
        self.use_celcius = use_celcius
        self.model = "RaspberryPi"

    def get_cpu_temperature_c(self):
        res = os.popen("vcgencmd measure_temp").readline()
        return float(res.replace("temp=", "").replace("'C\n", ""))

    def get_ram_usage_percent(self):
        p = os.popen("free")
        i = 0
        while 1:
            i = i + 1
            line = p.readline()
            if i == 2:
                # line = [total RAM, used RAM, free RAM]
                values = [int(t) for t in line.strip().split()[1:]]
                return int(100 * values[1] / values[0])

    def get_disk_usage_percent(self):
        p = os.popen("df -h /")
        i = 0
        while 1:
            i = i + 1
            line = p.readline()
            if i == 2:
                # line = [total disk space, used disk space, remaining disk space, percentage of disk used ]
                return int(line.split()[4].replace("%", ""))

    def get_reading(self):
        try:
            reading = {
                "disk_usage_%": self.get_disk_usage_percent(),
                "ram_usage_%": self.get_ram_usage_percent(),
            }
            if self.use_celcius:
                reading["cpu_temperature_C"] = self.get_cpu_temperature_c()
            else:
                reading["cpu_temperature_F"] = celcius_to_fahrenheit(
                    self.get_cpu_temperature_c()
                )
            return reading

        except Exception as e:
            logging.error("Failed to get %s sensor data...\n  %s" % (self.model, e))


class TemperatureMCP9808:
    def __init__(self, use_celcius=False, address=0x18):
        self._sensor = None
        self.address = address
        self.use_celcius = use_celcius
        self.model = "MCP9808"
        self.url = "https://learn.adafruit.com/adafruit-mcp9808-precision-i2c-temperature-sensor-guide"
        self._init_sensor()

    def _init_sensor(self):
        try:
            self._sensor = adafruit_mcp9808.MCP9808(board.I2C())
        except Exception as e:
            logging.error(
                "Failed to initialize %s ambient temp sensor...\n  %s" % (self.model, e)
            )

    def get_reading(self):
        try:
            if self.use_celcius:
                return {
                    "temperature_C": self._sensor.temperature,
                }
            else:
                return {
                    "temperature_F": celcius_to_fahrenheit(self._sensor.temperature),
                }
        except Exception as e:
            logging.error(
                "Failed to get %s ambient temp sensor data...\n  %s" % (self.model, e)
            )


class TemperatureHumidityPressureBME280:
    def __init__(self, use_celcius=False, address=0x76):
        self._sensor = None
        self.address = address
        self.use_celcius = use_celcius
        self.model = "BME280"
        self.url = "https://learn.adafruit.com/adafruit-bme280-humidity-barometric-pressure-temperature-sensor-breakout"
        self._init_sensor()

    def _init_sensor(self):
        try:
            self._sensor = adafruit_bme280.Adafruit_BME280_I2C(
                board.I2C(), address=self.address
            )
        except Exception as e:
            logging.error(
                "Failed to initialize %s temperature/humidity/pressure sensor...\n  %s"
                % (self.model, e)
            )

    def get_reading(self):
        try:
            if self.use_celcius:
                return {
                    "temperature_C": self._sensor.temperature,
                    "humidity_%": self._sensor.humidity,
                    "pressure_hPa": self._sensor.pressure,
                }
            else:
                return {
                    "temperature_F": celcius_to_fahrenheit(self._sensor.temperature),
                    "humidity_%": self._sensor.humidity,
                    "pressure_hPa": self._sensor.pressure,
                }
        except Exception as e:
            logging.error(
                "Failed to get %s temperature/humidity/pressure data...\n  %s"
                % (self.model, e)
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
            return {"lux": self._sensor.lux}
        except Exception as e:
            logging.error("Failed to get %s lux sensor data...\n  %s" % (self.model, e))


class AmbientLightTSL2591:
    def __init__(self, address=0x29, gain=adafruit_tsl2591.GAIN_LOW):
        self._sensor = None
        self.address = address
        self.gain = gain
        self.model = "TSL2591"
        self.url = "https://learn.adafruit.com/adafruit-tsl2591"
        self._init_sensor()

    def _init_sensor(self):
        try:
            self._sensor = adafruit_tsl2591.TSL2591(board.I2C())
            self._sensor.gain = self.gain

        except Exception as e:
            logging.error(
                "Failed to initialize %s lux sensor...\n  %s" % (self.model, e)
            )

    def get_reading(self):
        try:
            return {
                "lux": self._sensor.lux,
                "infrared": self._sensor.infrared,
                "visible": self._sensor.visible,
            }
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

