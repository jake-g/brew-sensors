#!/usr/bin/python
from __future__ import print_function

import argparse
import logging
import time

import sensors
from loggers import gSheetLogger


def main(args):
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('Debug logging enabled...')
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        gsheet = gSheetLogger(key_file=args.gsheet_secret, gsheet_name=args.gsheet_name)

    except Exception as e:
        logging.error('Failed to fetch gsheet: %s...\n%s' % (args.gsheet_name, e))

    if not gsheet.header():
        default_header = ['Timestamp', 'Local Temp (F)', 'Ambient Temp (F)', 'Carboy Temp (F)', 'Carboy Gravity']
        gsheet.insert_header(default_header)

    if args.log_period < 90:
        logging.warning(
            'log_period=%d: DarkSky api only allows fetching 1000 times per day (every ~90 seconds)' % args.log_period)

    logging.info(
        'Logging temp in F every %0.1f seconds to %s\n\nPress Ctrl-C to quit.' % (args.log_period, args.log_file))

    sensors_to_log = {
        'clock': sensors.Timestamp(timezone=args.timezone),
        'local_forcast': sensors.Forcast(args.darksky_api_key, args.lat, args.lng),
        'tilt': sensors.TiltHydrometer(args.tilt_color),
        'ambient_temp': sensors.TemperatureMCP9808()
    }
    last_backup = time.time()
    while True:
        res = {k: s.get_result() for k, s in sensors_to_log.items()}
        # TODO maybe log all info in seonsr dict? need to remove unneded keys (like unit) and make keys unique
        gsheet.sheet.append_row([
            res['clock']['time'],
            res['local_forcast']['temperature'],
            res['ambient_temp']['temperature'],
            res['tilt_temp']['temperature'],
            res['tilt_temp']['gravity']
        ])
        logging.debug('Last 5 entries:\n%s\n' % gsheet.get_df())
        logging.debug('Sleeping for %d seconds' % args.log_period)
        if (time.time() - last_backup) > args.backup_period:
            gsheet.dump_sheet('log_backup.tsv')

        time.sleep(args.log_period)

# TODO add backup to file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log various sensors related to homebrew")
    parser.add_argument("--log_file", default='log.tsv', help="CSV filename for log output", type=str)
    parser.add_argument("--log_period", default=120, help="How frequently (seconds) to log", type=float)
    parser.add_argument("--backuo_period", default=60*20, help="How frequently (seconds) to backup data to file", type=float)
    parser.add_argument("--tilt_color", default='black', help="Color of the tilt you want to check", type=str)
    parser.add_argument("--lat", default=47.6540872, help="Current location latitude", type=float)
    parser.add_argument("--lng", default=-122.3340208, help="Current location longitude", type=float)
    parser.add_argument("--timezone", default='US/Pacific', help="Timestamp timezone.", type=str)
    parser.add_argument("--darksky_api_key", default='d0693663c82510afb4d62edcc8355980',
                        help="API key for darksky forcast", type=str)
    parser.add_argument("--gsheet_secret", default='auth/secret.json',
                        help="json from GDrive api, see: https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html",
                        type=str)
    parser.add_argument("--gsheet_name", default='homebrew-log', help="Name of valid Google Sheet file.", type=str)
    parser.add_argument("--debug", help="Print debug info", action="store_true")
    args = parser.parse_args()

    main(args)
