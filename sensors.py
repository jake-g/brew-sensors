import logging
from datetime import datetime
import os
import time
import requests

from pytz import timezone
import board

######## i2c ##########
# INA219 - High Side DC Current Sensor
# Used to measure DC voltage, current, power, and energy
import adafruit_ina219
# INA260 - High/Low Side DC Current Sensor
# Used to measure voltage, current, power, and energy for both high and low-side applications
import adafruit_ina260
# BH1750 - Light Sensor
# Used to measure ambient light intensity
import adafruit_bh1750
# VEML6070 - UV Light Sensor
# Used to measure the intensity of ultraviolet (UV) light
import adafruit_veml6070
# VEML7700 - Ambient Light Sensor
# Used to measure ambient light intensity, with high precision and dynamic range
import adafruit_veml7700
# TSL2591 - Light Sensor
# Used to measure ambient light intensity with both visible and infrared light sensors
import adafruit_tsl2591
# MCP9808 - Temperature Sensor
# Used to measure ambient temperature with high accuracy
import adafruit_mcp9808
# BME280 - Temperature, Humidity, and Barometric Pressure Sensor
# Used to measure temperature, humidity, and barometric pressure
import adafruit_bme280
# SGP30 - Air Quality Sensor
# Used to measure indoor air quality (TVOC and CO2eq)
import adafruit_sgp30


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


class ForcastOpenWeather:

    def __init__(self, api_key, lat, lng, use_celcius=False, rate_limit_seconds=180):
        self.api_key = api_key
        self.lat = lat
        self.lng = lng
        self.use_celcius = use_celcius
        self.last_reading = None
        self.last_reading_timestamp = 0
        self.rate_limit_seconds = rate_limit_seconds
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def get_reading(self):
        try:
            url = f"{self.base_url}?lat={self.lat}&lon={self.lng}&appid={self.api_key}&units=imperial"
            last_reading_delta = time.time() - self.last_reading_timestamp
            if last_reading_delta > self.rate_limit_seconds:
                res = requests.get(url).json()
                reading = {
                    "temperature_F": res["main"]["temp"],
                    "pressure": res["main"]["pressure"],
                    "apparentTemperature": res["main"]["feels_like"],
                    "humidity": res["main"]["humidity"],
                    "cloudCover": res["clouds"]["all"],
                    "sunrise": res["sys"]["sunrise"],
                    "sunset": res["sys"]["sunset"],
                    "time": res["dt"],
                    "condition": res["weather"][0]["main"],
                    "summary": res["weather"][0]["description"],
                    "icon": res["weather"][0]["icon"],
                    "location": res["name"],
                    "windSpeed": res["wind"]["speed"],
                    "windGust": res["wind"]["gust"],
                    "windBearing": res["wind"]["deg"],
                }
                self.last_reading = reading.copy()
                self.last_reading_timestamp = time.time()
            else:
                logging.warning(
                    "Last reading was %ds ago which is less than the rate limit period of %ds, reusing last result..." % (
                        last_reading_delta, self.rate_limit_seconds)
                )
                reading = self.last_reading.copy()

            if self.use_celcius:
                reading["temperature_C"] = fahrenheit_to_celcius(
                    reading.pop("temperature_F", None)
                )
            return reading

        except Exception as e:
            logging.error("Failed to get OpenWeatherMap data...\n  %s" % e)


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
                self._sensor = adafruit_ina219.INA219(
                    board.I2C(), addr=self.address)
            else:
                self._sensor = adafruit_ina219.INA219(board.I2C())
        except Exception as e:
            logging.error(
                "Failed to initialize %s current sensor...\n  %s" % (
                    self.model, e)
            )

    def get_reading(self):
        try:
            return {
                # voltage on V- (load side)
                "voltage": self._sensor.bus_voltage,
                "current": self._sensor.current,  # current in mA
                # voltage between V+ and V- across the shunt
                "shunt_voltage": self._sensor.shunt_voltage,
            }
        except Exception as e:
            logging.error(
                "Failed to get %s current sensor data...\n  %s" % (
                    self.model, e)
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
                self._sensor = adafruit_ina260.INA260(
                    board.I2C(), address=self.address)
            else:
                self._sensor = adafruit_ina260.INA260(board.I2C())
        except Exception as e:
            logging.error(
                "Failed to initialize %s current sensor...\n  %s" % (
                    self.model, e)
            )

    def get_reading(self):
        try:
            # print('Shunt: %s\t%0.2f V\t%0.2f mA\t%0.2f W'% (hex(self.address),
            # self._sensor.voltage, self._sensor.current, self._sensor.power/1000.0))
            return {
                "voltage": self._sensor.voltage,  # voltage on V- (load side)
                "current": self._sensor.current,  # current in mA
                "power": self._sensor.power,
            }
        except Exception as e:
            logging.error(
                "Failed to get %s current sensor data...\n  %s" % (
                    self.model, e)
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
            logging.error("Failed to get %s sensor data...\n  %s" %
                          (self.model, e))


class AirQualitySGP30:
    def __init__(self, use_celcius=False, address=0x58):
        self._sensor = None
        self.address = address
        self.model = "SGP30"
        self.url = "https://learn.adafruit.com/adafruit-sgp30-gas-tvoc-eco2-mox-sensor/overview"
        self._init_sensor()

    def _init_sensor(self):
        try:
            self._sensor = adafruit_sgp30.Adafruit_SGP30(board.I2C())
        except Exception as e:
            logging.error(
                "Failed to initialize %s air quality sensor...\n  %s" % (
                    self.model, e)
            )
        self._set_temperature_humidity()

    def _set_temperature_humidity(self):
        try:  # get calibration temp / humidity
            reading = TemperatureHumidityPressureBME280(
                use_celcius=True).get_reading()
            self._sensor.set_iaq_relative_humidity(celsius=reading["temperature_C"],
                                                   relative_humidity=reading["humidity_%"])
        except Exception as e:
            logging.warning(
                "Failed to get baseline from TemperatureHumidityPressureBME280...\n  %s" % e
            )

    def get_reading(self):
        self._set_temperature_humidity()
        try:
            return {
                "TVOC": self._sensor.TVOC,
                "eCO2": self._sensor.eCO2,
            }
        except Exception as e:
            logging.error(
                "Failed to get %s  air quality sensor data...\n  %s" % (
                    self.model, e)
            )


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
                "Failed to initialize %s ambient temp sensor...\n  %s" % (
                    self.model, e)
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
                "Failed to get %s ambient temp sensor data...\n  %s" % (
                    self.model, e)
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
                    "humidity_%": self._sensor.humidity / 100.0,
                    "pressure_hPa": self._sensor.pressure,
                }
        except Exception as e:
            logging.error(
                "Failed to get %s temperature/humidity/pressure data...\n  %s"
                % (self.model, e)
            )


class LightBH1750:
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
            logging.error(
                "Failed to get %s lux sensor data...\n  %s" % (self.model, e))


class LightIrVisTSL2591:
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
                "Failed to initialize %s lux ir sensor...\n  %s" % (
                    self.model, e)
            )

    def get_reading(self):
        try:
            return {
                "lux": self._sensor.lux,
                "infrared": self._sensor.infrared,
                "visible": self._sensor.visible,
            }
        except Exception as e:
            logging.error(
                "Failed to get %s lux ir sensor data...\n  %s" % (self.model, e))


class LightVisVEML7700:
    def __init__(self, address=0x10):
        self._sensor = None
        self.address = address
        self.model = "VEML7700"
        self.url = (
            "https://learn.adafruit.com/adafruit-veml7700/overview"
        )
        self._init_sensor()

    def _init_sensor(self):
        try:
            self._sensor = adafruit_veml7700.VEML7700(board.I2C())
        except Exception as e:
            logging.error(
                "Failed to initialize %s lux sensor...\n  %s" % (self.model, e)
            )

    def get_reading(self):
        try:
            return {
                "lux": self._sensor.lux,
                "visible": self._sensor.light,
            }
        except Exception as e:
            logging.error(
                "Failed to get %s lux sensor data...\n  %s" % (self.model, e))


class LightUvVEML6070:
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
            logging.error("Failed to get %s UV sensor data...\n  %s" %
                          (self.model, e))
