from __future__ import print_function

import argparse
import time
import logging

import bluetooth._bluetooth as bluez
import blescan

from sensors import celcius_to_fahrenheit

TILTS = {
    "a495bb10c5b14b44b5121370f02d74de": "Red",
    "a495bb20c5b14b44b5121370f02d74de": "Green",
    "a495bb30c5b14b44b5121370f02d74de": "Black",
    "a495bb40c5b14b44b5121370f02d74de": "Purple",
    "a495bb50c5b14b44b5121370f02d74de": "Orange",
    "a495bb60c5b14b44b5121370f02d74de": "Blue",
    "a495bb70c5b14b44b5121370f02d74de": "Pink",
}


class TiltHydrometerSensor:
    def __init__(self, color, use_celcius=False):
        self.color = color
        self.use_celcius = use_celcius
        self.last_reading = None

    def get_reading(self):
        try:
            tilt_reading = get_tilt(self.color)
            if self.use_celcius:
                reading = {
                    "temperature_C": fahrenheit_to_celcius(tilt_reading.get_temp_f()),
                    "gravity": tilt_reading.get_gravity(),
                }
            else:
                reading = {
                    "temperature_F": tilt_reading.get_temp_f(),
                    "gravity": tilt_reading.get_gravity(),
                }
            self.last_reading = reading
            return reading

        except Exception as e:
            logging.error("Failed to get Tilt data...\n  %s" % e)
            if self.last_reading is not None:
                logging.info("Returning last tilt response.")
                return self.last_reading
            else:
                logging.error("No last tilt reading, returning None.")


class Tilt:
    def __init__(self, uuid, color, temp, gravity):
        self.uuid = uuid
        self.color = color
        self.temp = temp
        self.gravity = gravity

    def get_temp_f(self):
        return float(self.temp)

    def get_gravity(self):
        return float(self.gravity) / 1000

    def __str__(self, celcius=True):
        return "UUID: {u} Color: {c} Temp: {t} Gravity {g}".format(
            u=self.uuid, c=self.color, t=self.get_temp_f(), g=self.get_gravity()
        )


def get_tilt(color, tries=3):
    dev_id = 0
    try:
        sock = bluez.hci_open_dev(dev_id)
        # print "ble thread started"

    except:
        print
        "error accessing bluetooth device..."
        if tries > 1:
            time.sleep(1)
            return get_tilt(color, tries - 1)
        else:
            return False

    blescan.hci_le_set_scan_parameters(sock)
    blescan.hci_enable_le_scan(sock)

    all_tilts = {}
    returnedList = blescan.parse_events(sock, 100)
    for beacon in returnedList:
        if beacon["uuid"] in TILTS:
            this_tilt = Tilt(
                beacon["uuid"], TILTS[beacon["uuid"]], beacon["major"], beacon["minor"]
            )
            if this_tilt.color.lower() == color.lower():
                return this_tilt
            else:
                all_tilts[this_tilt.color] = this_tilt

    return all_tilts


def main(args):
    color = args.color
    tilt = get_tilt(color)
    if not tilt:
        print("Could not find a tilt of color {c}".format(c=color))
    if isinstance(tilt, list):
        print("Found these though: {o}".format(",".join(tilt.keys())))
    if isinstance(tilt, Tilt):
        if args.temp:
            print(tilt.get_temp_f())
        elif args.gravity:
            print(tilt.get_gravity())
        else:
            print(str(tilt))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get output from a Tilt Hydrometer")
    parser.add_argument("color", help="Color of the tilt you want to check", type=str)
    parser.add_argument("--temp", help="Output temperature only", action="store_true")
    parser.add_argument("--gravity", help="Output gravity only", action="store_true")
    parser.add_argument(
        "--use_celcius",
        help="Output as fahrenheit rather than celcius",
        action="store_true",
    )
    args = parser.parse_args()

    main(args)
