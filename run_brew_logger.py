import os
import time

import sensors
import tilt
from runner import main

cwd = os.path.dirname(os.path.realpath(__file__))
# for service on pi see: /lib/systemd/system/homebrew-sensor-logging.service
# Local Parameters
GPS_LAT = 47.677601
GPS_LNG = 122.369141
TIMEZONE = "US/Pacific"

# Color of the tilt sensor to log
TILT_COLOR = "black"
STARTING_GRAVITY = 1.058

# Darksyk API Auth token.
DARKSKY_AUTH = "d0693663c82510afb4d62edcc8355980"

# Dictionary mapping sensor name to sensor objects to be logged
SENSOR_MAP = {
    "clock": sensors.Timestamp(timezone=TIMEZONE),
    "forecast": sensors.Forecast(DARKSKY_AUTH, GPS_LAT, GPS_LNG),
    "tilt": tilt.TiltHydrometerSensor(TILT_COLOR, sg=STARTING_GRAVITY),
    "pi": sensors.PiSensors(),
    "ambient": sensors.TemperatureMCP9808(),
    "light": sensors.AmbientLightBH1750(),
    "sun": sensors.UvVEML6070(),
}

# Configuration for sensor logging.
LOG_CONF = {
    # Extra stdout logging verbosity for debug purposes
    "debug": False,
    # Name of local .tsv file for logging session.
    "local_logfile": os.path.join(cwd, "brew-logs/log_%d.tsv" % time.time()),
    # Log data every LOG_PERIOD seconds.
    "log_period": 60 * 5,
    # Name of local .tsv file to backup data to.
    "local_backup": os.path.join(cwd, "brew-logs/gsheet_bkp.tsv"),
    # Backup data locally every LOG_PERIOD seconds.
    "backup_period": 60 * 20,
    # Name of Google Spreadsheet to write to.
    "gsheet_name": "brew-log",
    # Maximum number of decimal places for entry.
    "max_precision": 4,
    # Authentication json for GDrive api.
    # see:
    # https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html
    "gsheet_auth": os.path.join(cwd, "auth/brew-secret.json"),
    # This is used to validate the logging header matches in all places
    # (gsheet, local, ect).
    "expected_header": [
        "clock_time",
        "tilt_gravity",
        "tilt_alcohol_%",
        "tilt_temperature_F",
        "ambient_temperature_F",
        "light_lux",
        "sun_uv",
        "pi_ram_usage_%",
        "pi_disk_usage_%",
        "pi_cpu_temperature_F",
        "forecast_temperature_F",
        "forecast_humidity",
        "forecast_pressure",
        "forecast_apparentTemperature",
        "forecast_cloudCover",
        "forecast_dewPoint",
        "forecast_icon",
        "forecast_nearestStormBearing",
        "forecast_nearestStormDistance",
        "forecast_ozone",
        "forecast_precipIntensity",
        "forecast_precipProbability",
        "forecast_summary",
        "forecast_time",
        "forecast_uvIndex",
        "forecast_visibility",
        "forecast_windBearing",
        "forecast_windGust",
        "forecast_windSpeed",
    ],
}

if __name__ == "__main__":
    main(SENSOR_MAP, LOG_CONF)
