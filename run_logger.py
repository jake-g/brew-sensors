#!/usr/bin/python
from __future__ import print_function

import argparse
import logging
import time

import sensors
from loggers import gSheetLogger, TsvLogger

expected_header = ['clock_time', 'tilt_temperature', 'tilt_gravity', 'ambient_temperature',
                   'local_temperature', 'local_humidity', 'local_pressure',
                   'local_apparentTemperature', 'local_cloudCover', 'local_dewPoint',
                   'local_icon', 'local_nearestStormBearing', 'local_nearestStormDistance',
                   'local_ozone', 'local_precipIntensity', 'local_precipProbability',
                   'local_summary', 'local_time', 'local_uvIndex', 'local_visibility',
                   'local_windBearing', 'local_windGust', 'local_windSpeed']


def init_gsheet(args):
    try:
        gsheet = gSheetLogger(key_file=args.gsheet_secret, gsheet_name=args.gsheet_name,
                              sheet_idx=1 if args.debug else 0)  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    except Exception as e:
        logging.error('Failed to fetch gsheet: %s...\n%s' % (args.gsheet_name, e))

    if not gsheet.header:
        gsheet.insert_header(expected_header)
    elif gsheet.header != expected_header:
        logging.warning('Expected header differs from gsheet header!\n expected (len=%d): %s\n gsheet (len=%d): %s' % (
            len(expected_header), expected_header, len(gsheet.header), gsheet.header))
    return gsheet

def main(args):
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('Debug logging enabled...')
    else:
        logging.basicConfig(level=logging.INFO)

    tsv_log = TsvLogger(args.log_file, expected_header)
    gsheet = init_gsheet(args)

    if args.log_period < 90:
        logging.warning(
            'log_period=%d: DarkSky api only allows fetching 1000 times per day (every ~90 seconds)' % args.log_period)

    logging.info('Logging temp in F every %0.1f seconds to %s.' % (args.log_period, args.gsheet_name))
    logging.info(
        'Backing up %s every %0.1f seconds to %s' % (args.gsheet_name, args.backup_period, args.backup_log_file))
    print('Press Ctrl-C to quit.')
    sensors_to_log = {
        'clock': sensors.Timestamp(timezone=args.timezone),
        'local': sensors.Forcast(args.darksky_api_key, args.lat, args.lng),
        'tilt': sensors.TiltHydrometer(args.tilt_color),
        'ambient': sensors.TemperatureMCP9808()
    }
    last_backup = time.time()
    while True:
        # TODO multiprocess this
        sensor_readings = {k: s.get_reading() for k, s in sensors_to_log.items()}
        row_dict = {'%s_%s' % (sns, key): value for sns, res in sensor_readings.items() for key, value in res.items()}
        row = [row_dict.get(k, '') for k in expected_header]
        try:
            gsheet.sheet.append_row(row)
            logging.debug('First 5 columns of last 5 entries:\n%s\n' % gsheet.get_df()[expected_header[0:5]])
        except Exception as e:
            logging.error('Failed to append to gsheet: %s...\n%s' % (args.gsheet_name, e))
        try:
            tsv_log.append_row(row)
        except Exception as e:
            logging.error('Failed to append to tsv: %s...\n%s' % (args.log_file, e))


        if (time.time() - last_backup) > args.backup_period:
            gsheet.dump_sheet(args.backup_log_file)
            last_backup = time.time()
        logging.debug('Sleeping for %d seconds' % args.log_period)
        time.sleep(args.log_period)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log various sensors related to homebrew")
    parser.add_argument("--log_period", default=60 * 5, help="How frequently (s) to log", type=float)
    parser.add_argument("--gsheet_secret", default='./auth/secret.json',
                        help="json from GDrive api, see: https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html",
                        type=str)
    parser.add_argument("--gsheet_name", default='homebrew-log', help="Name of valid Google Sheet file.", type=str)
    parser.add_argument("--log_file", default='./logs/log_%d.tsv' % time.time(), help="CSV filename for log output",
                        type=str)
    parser.add_argument("--backup_log_file", default='./logs/gsheet_bkp.tsv', help="TSV filename for log output",
                        type=str)
    parser.add_argument("--backup_period", default=60 * 60, help="How frequently (s) to backup to file", type=float)
    parser.add_argument("--tilt_color", default='black', help="Color of the tilt you want to check", type=str)
    parser.add_argument("--lat", default=47.654049, help="Current location latitude", type=float)
    parser.add_argument("--lng", default=-122.334159, help="Current location longitude", type=float)
    parser.add_argument("--timezone", default='US/Pacific', help="Timestamp timezone.", type=str)
    parser.add_argument("--darksky_api_key", default='d0693663c82510afb4d62edcc8355980',
                        help="API key for darksky forcast", type=str)
    parser.add_argument("--debug", help="Print debug info", action="store_true")
    args = parser.parse_args()

    main(args)
