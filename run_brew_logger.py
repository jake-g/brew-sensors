import os
import sensors
import tilt
from runner import main

BEER_NAME = "american_session"
STARTING_GRAVITY = 1.039

# Local Parameters
GPS_LAT = 47.671866
GPS_LNG = -122.394456
TIMEZONE = "US/Pacific"

# Color of the tilt sensor to log
TILT_COLOR = "black"
# Open Weather API Key
OPENWEATHER_AUTH = "PLACEHOLDER"
# Dictionary mapping sensor name to sensor objects to be logged
SENSOR_MAP = {
    "clock": sensors.Timestamp(timezone=TIMEZONE),
    "forecast": sensors.ForcastOpenWeather(OPENWEATHER_AUTH, GPS_LAT, GPS_LNG),
    "beer": tilt.TiltHydrometerSensor(TILT_COLOR, sg=STARTING_GRAVITY),
    "amb": sensors.TemperatureHumidityPressureBME280(),
    "air": sensors.AirQualitySGP30(),
    "light": sensors.LightIrVisTSL2591(),
    "light_uv": sensors.LightUvVEML6070(),
    "pi": sensors.PiSensors(),
}
print('brewing %s with SG: %0.2f' % (BEER_NAME, STARTING_GRAVITY))
print('logging sensors: %s' % sorted(SENSOR_MAP.keys()))

# Configuration for sensor logging.
cwd = os.path.dirname(os.path.realpath(__file__))
name_key = BEER_NAME.lower().replace(' ', '_')
LOG_CONF = {
    # Extra stdout logging verbosity for debug purposes
    "debug": True,
    # Name of local .tsv file for logging session.
    "local_logfile": os.path.join(cwd, "brew-logs/log_%s.tsv" % name_key),
    # Log data every LOG_PERIOD seconds.
    "log_period": 60 * 5,
    # Name of local .json status file for session sensor status
    "local_json_path":   os.path.join(cwd, "brew-logs"),
    # Name of local .tsv file to backup data to.
    "local_backup": os.path.join(cwd, "brew-logs/gsheet_bkp.tsv"),
    # Backup data locally every LOG_PERIOD seconds.
    "backup_period": 60 * 20,
    # Name of Google Spreadsheet to write to.
    "gsheet_name": "brew-log",
    # Maximum number of decimal places for entry.
    "max_precision": 4,
    # Authentication json for GDrive api.
    # https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html
    "gsheet_auth": os.path.join(cwd, "auth/brew-secret.json"),
    # This is used to validate the logging header matches in all places
    # (gsheet, local, ect).
    "expected_header": [
        "clock_time",
        "beer_gravity",
        "beer_alcohol_%",
        "beer_temperature_F",
        "amb_temperature_F",
        "amb_humidity_%",
        "amb_pressure_hPa",
        "air_TVOC",
        "air_eCO2",
        "light_lux",
        "light_ir",
        "light_vis",
        "light_uv_uv",
        "light_uv_uv_index",
        "pi_ram_usage_%",
        "pi_disk_usage_%",
        "pi_cpu_temperature_F",
        "forecast_temperature_F",
        "forecast_humidity",
        "forecast_pressure",
        "forecast_apparentTemperature",
        "forecast_cloudCover",
        "forecast_sunrise",
        "forecast_sunset",
        "forecast_condition",
        "forecast_icon",
        "forecast_summary",
        "forecast_location",
        "forecast_time",
        "forecast_windBearing",
        "forecast_windGust",
        "forecast_windSpeed",
    ],
}

if __name__ == "__main__":
    main(SENSOR_MAP, LOG_CONF)
