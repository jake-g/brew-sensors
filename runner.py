from __future__ import print_function

import logging
import time
import json

from loggers import gSheetLogger, TsvLogger


def main(sensor_map, log_conf):

    # Init Logging
    if log_conf["debug"] == True:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Debug logging enabled...")
    else:
        logging.basicConfig(level=logging.INFO)
    # Logging to local .tsv file.
    tsv_log = TsvLogger(log_conf["local_logfile"], log_conf["expected_header"])

    logging.info("Logging sensors every %0.1f seconds" % log_conf["log_period"])
    # Logging to Google Sheet.
    if log_conf["gsheet_auth"] and log_conf["gsheet_name"]:
        gsheet = gSheetLogger(
            key_file=log_conf["gsheet_auth"],
            gsheet_name=log_conf["gsheet_name"],
            header=log_conf["expected_header"],
            sheet_idx=0,
        )
        logging.info(
            "Backing up %s every %0.1f seconds to %s"
            % (
                log_conf["gsheet_name"],
                log_conf["backup_period"],
                log_conf["gsheet_name"],
            )
        )

    # Main Loop
    print("Press Ctrl-C to quit.")
    last_backup = time.time()
    last_readings = {}
    while True:
        try:
            readings = {}
            for sensor_name, sensor_obj in sensor_map.items():
                res_dict = sensor_obj.get_reading()
                if res_dict:
                    for key, value in res_dict.items():
                        entry_name = "%s_%s" % (sensor_name, key)
                        if entry_name in log_conf["expected_header"]:
                            if isinstance(value, float):
                                value = round(value, log_conf["max_precision"])
                            readings[entry_name] = value

            row = []
            for key in log_conf["expected_header"]:
                if key in readings:
                    row.append(readings[key])
                elif key in last_readings:
                    logging.warning(
                        "New data entry missing key: %s using last entry..." % key
                    )
                    row.append(last_readings[key])
                else:
                    logging.warning(
                        "New and previous data entry missing key: %s, setting to None..."
                        % key
                    )
                    row.append("")
            last_readings = readings

            # Log new entry
            if tsv_log:
                try:
                    tsv_log.append_row(row)
                except Exception as e:
                    logging.error(
                        "Failed to append to tsv: %s...\n%s"
                        % (log_conf["local_logfile"], e)
                    )
                    logging.error(
                        "Trying to re-initialize tsv: %s..." % log_conf["local_logfile"]
                    )
                    tsv_log = TsvLogger(
                        log_conf["local_logfile"], log_conf["expected_header"]
                    )

            if gsheet.sheet:
                try:
                    gsheet.sheet.append_row(row)
                except Exception as e:
                    logging.error(
                        "Failed to append to gsheet: %s...\n%s"
                        % (log_conf["gsheet_name"], e)
                    )
                    logging.error(
                        "Trying to re-initialize gsheet: %s..."
                        % log_conf["gsheet_name"]
                    )
                    gsheet = gSheetLogger(
                        key_file=log_conf["gsheet_auth"],
                        gsheet_name=log_conf["gsheet_name"],
                        header=log_conf["expected_header"],
                        sheet_idx=0,
                    )
                    gsheet.sheet.append_row(row)


            # Maybe backup the data.
            last_backup_elapsed = time.time() - last_backup
            logging.debug("Last backup %d seconds seconds ago" % last_backup_elapsed)
            logging.debug(
                "Next backup %d in seconds"
                % (log_conf["backup_period"] - last_backup_elapsed)
            )
            if last_backup_elapsed > log_conf["backup_period"]:
                gsheet.dump_sheet(log_conf["local_backup"])
                last_backup = time.time()

            logging.debug(json.dumps(readings, sort_keys=True, indent=2))

        except Exception as e:
            logging.error("Failed in main loop...\n%s" % e)
            logging.error("\ndebug this, it means an error went uncaught!\n")

        logging.debug("Sleeping for %d seconds" % log_conf["log_period"])
        time.sleep(log_conf["log_period"])
