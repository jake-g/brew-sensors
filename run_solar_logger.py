import time

import sensors
from runner import main

# Local Parameters
GPS_LAT = 47.677601
GPS_LNG = 122.369141
TIMEZONE = "US/Pacific"

# I2C Addresses for multiple sensors
CHARGE_I2C_ADDR = 0x44  # A1 jumped
LOAD_I2C_ADDR = 0x41  # A0 jumped

# Darksyk API Auth token.
DARKSKY_AUTH = "d0693663c82510afb4d62edcc8355980"

# Dictionary mapping sensor name to sensor objects to be logged
SENSOR_MAP = {
    "CLOCK": sensors.Timestamp(timezone=TIMEZONE),
    "FORCAST": sensors.Forcast(DARKSKY_AUTH, GPS_LAT, GPS_LNG),
    "UV": sensors.UvVEML6070(),
    "LIGHT": sensors.AmbientLightTSL2591(),
    "AMBIENT": sensors.TemperatureHumidityPressureBME280(),
    "MPTT_IN": sensors.HighSideCurrentINA219(address=CHARGE_I2C_ADDR),
    "MPTT_OUT": sensors.HighSideCurrentINA219(address=LOAD_I2C_ADDR),
}

# Configuration for sensor logging.
LOG_CONF = {
    # Extra stdout logging verbosity for debug purposes
    "debug": True,
    # Name of local .tsv file for logging session.
    "local_logfile": "./solar-logs/log_%d.tsv" % time.time(),
    # Log data every LOG_PERIOD seconds.
    "log_period": 60 * 3,
    # Name of local .tsv file to backup data to.
    "local_backup": "./solar-logs/gsheet_bkp.tsv",
    # Backup data locally every LOG_PERIOD seconds.
    "backup_period": 60 * 20,
    # Name of Google Spreadsheet to write to.
    "gsheet_name": "solar-log",
    # Maximum number of decimal places for entry.
    "max_precision": 4,
    # Authentication json for GDrive api.
    # see:
    # https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html
    "gsheet_auth": "./auth/solar-secret.json",
    # This is used to validate the logging header matches in all places
    # (gsheet, local, ect).
    "expected_header": [
        "CLOCK_time",
        "LIGHT_lux",
        "LIGHT_infrared",
        "LIGHT_visible",
        "UV_uv",
        "UV_uv_index",
        "AMBIENT_temperature_F",
        "AMBIENT_humidity_%",
        "AMBIENT_pressure_hPa",
        "MPTT_IN_load_current",
        "MPTT_IN_load_voltage",
        "MPTT_IN_shunt_voltage",
        "MPTT_OUT_load_current",
        "MPTT_OUT_load_voltage",
        "MPTT_OUT_shunt_voltage",
        "FORCAST_temperature",
        "FORCAST_humidity",
        "FORCAST_pressure",
        "FORCAST_apparentTemperature",
        "FORCAST_cloudCover",
        "FORCAST_dewPoint",
        "FORCAST_icon",
        "FORCAST_nearestStormBearing",
        "FORCAST_nearestStormDistance",
        "FORCAST_ozone",
        "FORCAST_precipIntensity",
        "FORCAST_precipProbability",
        "FORCAST_summary",
        "FORCAST_time",
        "FORCAST_uvIndex",
        "FORCAST_visibility",
        "FORCAST_windBearing",
        "FORCAST_windGust",
        "FORCAST_windSpeed",
    ],
}

if __name__ == "__main__":
    main(SENSOR_MAP, LOG_CONF)
