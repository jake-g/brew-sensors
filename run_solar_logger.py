#!/usr/bin/python
from __future__ import print_function

import argparse
import logging
import time
import json

import sensors
from loggers import gSheetLogger, TsvLogger

def main(args, sensors_to_log, expected_header):
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('Debug logging enabled...')
    else:
        logging.basicConfig(level=logging.INFO)

    tsv_log = TsvLogger(args.log_file, expected_header)
    gsheet = gSheetLogger(key_file=args.gsheet_secret, gsheet_name=args.gsheet_name, header=expected_header,
                          sheet_idx=1 if args.debug else 0)

    if args.log_period < 90:
        logging.warning(
            'log_period=%d: DarkSky api only allows fetching 1000 times per day (every ~90 seconds)' % args.log_period)

    logging.info('Logging sensors every %0.1f seconds to %s.' % (args.log_period, args.gsheet_name))
    logging.info(
        'Backing up %s every %0.1f seconds to %s' % (args.gsheet_name, args.backup_period, args.backup_log_file))
    print('Press Ctrl-C to quit.')

    last_backup = time.time()
    last_row_dict = {}
    while True:
        try:
            sensor_readings = {k: s.get_reading() for k, s in sensors_to_log.items()}  # TODO multiprocess this
            row_dict = {
                '%s_%s' % (sns, key): value for sns, res in
                sensor_readings.items() for key, value in res.items()
                }
            print(json.dumps(row_dict, sort_keys=True, indent=2))
            row = []
            for key in expected_header:
                if key in row_dict:
                    row.append(row_dict[key])
                elif key in last_row_dict:
                    logging.warning('New data entry missing key: %s using last entry...' % key)
                    row.append(last_row_dict[key])
                else:
                    logging.warning('New and previous data entry missing key: %s, setting to None...' % key)
                    row.append('')

            try:
                tsv_log.append_row(row)
            except Exception as e:
                logging.error('Failed to append to tsv: %s...\n%s' % (args.log_file, e))
                logging.error('Trying to re-initialize tsv: %s...' % args.log_file)
                tsv_log = TsvLogger(args.log_file, expected_header)

            try:
                gsheet.sheet.append_row(row)
                logging.debug('First 5 columns of last 5 entries:\n%s\n' % gsheet.get_df()[expected_header[0:5]])
            except Exception as e:
                logging.error('Failed to append to gsheet: %s...\n%s' % (args.gsheet_name, e))
                logging.error('Trying to re-initialize gsheet: %s...' % args.gsheet_name)
                gsheet = gSheetLogger(key_file=args.gsheet_secret, gsheet_name=args.gsheet_name, header=expected_header,
                                      sheet_idx=1 if args.debug else 0)
            last_backup_elapsed = (time.time() - last_backup)
            last_row_dict = row_dict
            logging.debug('Last backup %d seconds seconds ago' % last_backup_elapsed)
            logging.debug('Next backup %d in seconds' % (args.backup_period - last_backup_elapsed))
            if last_backup_elapsed > args.backup_period:
                gsheet.dump_sheet(args.backup_log_file)
                last_backup = time.time()

        except Exception as e:
            logging.error('Failed in main loop...\n%s' % e)
            logging.error('\ndebug this, it means an error went uncaught!\n')

        logging.debug('Sleeping for %d seconds' % args.log_period)
        time.sleep(args.log_period)


if __name__ == "__main__":

    # Local Parameters
    GPS_LAT = 47.677601
    GPS_LNG = 122.369141
    TIMEZONE = 'US/Pacific'

    # Name of Google Spreadsheet to write to.
    GSHEET_NAME = 'solar-log'
    # Directory where local logs are saved to.
    LOCAL_TSV_DIR = './solar-logs/' #TODO make flag for this instead of flag for full path
    # Name of local .tsv file to backup data to.
    BACKUP_TSV = LOCAL_TSV_DIR + 'gsheet_bkp.tsv'
    # Name of local .tsv file for logging session.
    LOG_TSV = LOCAL_TSV_DIR + 'log_%d.tsv' % time.time()
    # Backup data locally every LOG_PERIOD seconds.
    BACKUP_PERIOD = 60*20
    # Log data every LOG_PERIOD seconds.
    LOG_PERIOD = 60*3 
    # Darksyk API Auth token.
    WEATHER_AUTH = 'd0693663c82510afb4d62edcc8355980'
    # Authentication json for GDrive api. 
    # see: https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html
    GSHEET_AUTH = './auth/solar-secret.json' 

    # I2C Addresses for multiple sensors
    CHARGE_I2C_ADDR= 0x44 # A1 jumped
    LOAD_I2C_ADDR=0x41 # A0 jumped

    HEADER = ['CLOCK_time', 'ALS_lux', 'UV_uv', 'UV_uv_index', 'TEMP_F_temperature',
                    'MPTT_IN_load_current', 'MPTT_IN_load_voltage', 'MPTT_IN_shunt_voltage', 
                    'MPTT_OUT_load_current', 'MPTT_OUT_load_voltage', 'MPTT_OUT_shunt_voltage',
                    'FORCAST_temperature', 'FORCAST_humidity', 'FORCAST_pressure',
                    'FORCAST_apparentTemperature', 'FORCAST_cloudCover', 'FORCAST_dewPoint',
                    'FORCAST_icon', 'FORCAST_nearestStormBearing', 'FORCAST_nearestStormDistance',
                    'FORCAST_ozone', 'FORCAST_precipIntensity', 'FORCAST_precipProbability',
                    'FORCAST_summary', 'FORCAST_time', 'FORCAST_uvIndex', 'FORCAST_visibility',
                    'FORCAST_windBearing', 'FORCAST_windGust', 'FORCAST_windSpeed']

    SENSORS = {
        'CLOCK': sensors.Timestamp(timezone=TIMEZONE),
        'FORCAST': sensors.Forcast(WEATHER_AUTH, GPS_LAT, GPS_LNG),
        'UV': sensors.UvVEML6070(),
        'ALS': sensors.AmbientLightBH1750(),
        'TEMP_F': sensors.TemperatureMCP9808(),
        'MPTT_IN': sensors.HighSideCurrentINA219(address=CHARGE_I2C_ADDR),
        'MPTT_OUT': sensors.HighSideCurrentINA219(address=LOAD_I2C_ADDR),
    }


    parser = argparse.ArgumentParser(description="Log various sensors related to the solar rig")
    parser.add_argument("--log_period", default=LOG_PERIOD, type=float, help="How frequently (s) to log")
    parser.add_argument("--gsheet_secret", default=GSHEET_AUTH, type=str,
                        help="json from GDrive api, see: https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html")
    parser.add_argument("--gsheet_name", default=GSHEET_NAME, type=str, help="Name of valid Google Sheet file.")
    parser.add_argument("--log_file", default=LOG_TSV, type=str,
                        help="CSV filename for log output.")
    parser.add_argument("--backup_log_file", default=BACKUP_TSV, type=str,
                        help="TSV filename for log output.")
    parser.add_argument("--backup_period", default=BACKUP_PERIOD, type=float, help="How frequently (s) to backup to file.")
    # parser.add_argument("--lat", default=47.677601, type=float, help="Current location latitude")
    # parser.add_argument("--lng", default=-122.369141, type=float, help="Current location longitude")
    # parser.add_argument("--timezone", default='US/Pacific', help="Timestamp timezone.", type=str)
    # parser.add_argument("--darksky_api_key", default='d0693663c82510afb4d62edcc8355980', type=str,
    #                     help="API key for darksky forcast")
    parser.add_argument("--debug", action="store_true", help="Print debug info")
    args = parser.parse_args()

    main(args, SENSORS, HEADER)
