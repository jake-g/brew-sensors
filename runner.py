from __future__ import print_function

import logging
import time
import json

from loggers import gSheetLogger, TsvLogger


def main(sensor_map, log_conf):
    # Init Logging
    logging.basicConfig(level=logging.INFO)
    if log_conf["debug"]:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Debug logging enabled...")
    # Logging to local .tsv file.
    tsv_log = TsvLogger(log_conf["local_logfile"], log_conf["expected_header"])

    if log_conf["log_period"] < 90:
        logging.warning(
            "log_period=%d: DarkSky api only allows fetching 1000 times per day (every ~90 seconds)"
            % log_conf["log_period"]
        )
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
    last_row_dict = {}
    while True:
        try:
            sensor_readings = {k: s.get_reading() for k, s in sensor_map.items()}
            row_dict = {
                "%s_%s" % (sns, key): value
                for sns, res in sensor_readings.items()
                for key, value in res.items()
            }
            logging.debug(json.dumps(row_dict, sort_keys=True, indent=2))

            row = []
            for key in log_conf["expected_header"]:
                if key in row_dict:
                    row.append(row_dict[key])
                elif key in last_row_dict:
                    logging.warning(
                        "New data entry missing key: %s using last entry..." % key
                    )
                    row.append(last_row_dict[key])
                else:
                    logging.warning(
                        "New and previous data entry missing key: %s, setting to None..."
                        % key
                    )
                    row.append("")
            last_row_dict = row_dict

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
                    logging.debug(
                        "First 5 columns of last 5 entries:\n%s\n"
                        % gsheet.get_df()[log_conf["expected_header"][0:5]]
                    )
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

        except Exception as e:
            logging.error("Failed in main loop...\n%s" % e)
            logging.error("\ndebug this, it means an error went uncaught!\n")

        logging.debug("Sleeping for %d seconds" % log_conf["log_period"])
        time.sleep(log_conf["log_period"])
