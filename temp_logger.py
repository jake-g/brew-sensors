#!/usr/bin/python
from __future__ import print_function

import argparse
import datetime
import logging
import os
import time

import Adafruit_MCP9808.MCP9808 as MCP9808
import forecastio
import pytz
from tilt import get_tilt


def c_to_f(c):
    return c * 9.0 / 5.0 + 32.0


class TsvLogger:
    def __init__(self, log_filename, header):
        self.file = log_filename
        self.n_cols = len(header)
        self.header = header
        self.init_log()

    def init_log(self):
        if not os.path.exists(self.file):
            logging.debug('Log file doesnt exist, creating it...')
            self.write_row(self.header)
        else:
            logging.debug('Appending to existing logfile %s...' % self.file)

    def write_row(self, row):
        if len(row) != self.n_cols:
            raise ValueError('row of length %d != %d n_cols' % (len(row), self.n_cols))
        row_str = '\t'.join([str(t) for t in row])
        logging.debug('Logging to file:\n%s' % row_str)
        with open(self.file, 'a') as f:
            f.write(row_str + '\n')


def main(args):
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('Debug logging enabled...')

    header = ['Timestamp', 'Local Temp (F)', 'Ambient Temp (F)', 'Carboy Temp (F)', 'Carboy Gravity']
    log = TsvLogger(args.log_file, header)

    if args.log_period < 90:
        logging.warning(
            'log_period=%d: DarkSky api only allows fetching forecast 1000 times per day (every ~90 seconds)' % args.log_period)

    try:  # Default constructor will use the default I2C address (0x18) and pick a default I2C bus.
        temp_sensor = MCP9808.MCP9808()
        temp_sensor.begin()
    except Exception as e:
        logging.error('Failed to initialize MCP9808 ambient temp sensor...\n%s' % e)

    logging.info(
        'Logging temp in F every %0.1f seconds to %s\n\nPress Ctrl-C to quit.' % (args.log_period, args.log_file))
    while True:
        current_time = datetime.datetime.now(pytz.utc).strftime("%m-%d-%Y %H:%M")

        try:
            darksky_forcast = forecastio.load_forecast(args.darksky_api_key, args.lat, args.lng).currently()
            darksky_temp = float(darksky_forcast.temperature)
        except Exception as e:
            logging.error('Failed to get DarkSky data...\n%s' % e)

        try:
            tilt_reading = get_tilt(args.tilt_color)
            tilt_temp = float(tilt_reading.get_temp(celcius=False))
            tilt_gravity = float(tilt_reading.get_gravity())
        except Exception as e:
            logging.error('Failed to get DarkSky data...\n%s' % e)

        try:
            ambient_temp = float(c_to_f(temp_sensor.readTempC()))
        except Exception as e:
            logging.error('Failed to get MCP9808 ambient temp sensor data...\n%s' % e)

        logging.debug('\n--------------------Sensor Readings--------------------\n')
        logging.debug('Current Time: %s' % current_time)
        logging.debug('Current Location: Latitude=%0.2f, Longitude=%0.2f ' % (args.lat, args.lng))
        logging.debug('Local Temperature: %0.1f F' % darksky_temp)
        # logging.debug('Tilt Color:\t%s (UUID=%s)' % (tilt_reading.color, tilt_reading.uuid))
        logging.debug('Carboy Temperature: %0.1f F' % tilt_temp)
        logging.debug('Carboy Gravity: %0.3f' % tilt_gravity)
        logging.debug('Ambient Temperature: %0.1f F' % ambient_temp)
        logging.debug('\n-------------------------------------------------------\n')

        row_entry = [current_time, darksky_temp, ambient_temp, tilt_temp, tilt_gravity]
        log.write_row(row_entry)
        time.sleep(args.log_period)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log various sensors related to homebrew")
    parser.add_argument("--log_file", default='log.tsv', help="CSV filename for log output", type=str)
    parser.add_argument("--log_period", default=120, help="How frequently (seconds) to log", type=float)
    parser.add_argument("--tilt_color", default='black', help="Color of the tilt you want to check", type=str)
    # parser.add_argument("--temp_unit", default='F', help="Temperature unit ('C' or 'F')", type=str)
    parser.add_argument("--lat", default=47.6540872, help="Current location latitude", type=float)
    parser.add_argument("--lng", default=-122.3340208, help="Current location longitude", type=float)
    parser.add_argument("--darksky_api_key", default='d0693663c82510afb4d62edcc8355980',
                        help="API key for darksky forcast", type=str)
    parser.add_argument("--debug", help="Print debug info", action="store_true")
    args = parser.parse_args()

    main(args)
