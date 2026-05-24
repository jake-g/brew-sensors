from __future__ import print_function

import http.server
import json
import logging
import os
import threading

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas


class gSheetLogger:
    def __init__(self, key_file, gsheet_name, sheet_idx=0, header=[]):
        self.name = gsheet_name
        self.sheet_idx = sheet_idx
        self.service_email = ""
        self.sheet = None
        self.header = None
        self.client = None
        self._authorize_client(key_file)
        self._get_sheet()
        if header:
            self.init_header(header)

    def _authorize_client(
        self,
        key_file,
        n_tries=5,
        scope=(
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ),
    ):
        try:
            tries = 0
            success = False
            while success is False and tries < n_tries:
                try:
                    tries += 1
                    creds = ServiceAccountCredentials.from_json_keyfile_name(key_file, scope)
                    self.service_email = str(creds.service_account_email)
                    self.client = gspread.authorize(creds)
                    success = True
                except Exception as e:
                    logging.warning("Failed %d times...\n Error: %s" % (tries, e))
        except Exception as e:
            logging.error("%s\nFailed to authenticate client..." % e)

    def _get_sheet(self):
        try:
            self.sheet = self.client.open(self.name).get_worksheet(self.sheet_idx)
            logging.debug("Sheet has %d rows" % len(self.sheet.get_all_values()))
        except Exception as e:
            logging.error(
                "%s\nEnsure files are shared with this email:\n\n  %s"
                % (e, self.service_email)
            )
        self._set_header()

    def _set_header(self):
        if self.sheet and self.sheet.row_values:
            self.header = self.sheet.row_values(1)
        else:
            logging.warning("Sheet has no header data!")

    def _insert_header(self, header):
        self.sheet.insert_row(header, 1)
        self._set_header()

    def get_df(self):
        self._set_header()
        return pandas.DataFrame(self.sheet.get_all_records(), columns=self.header)

    def dump_sheet(self, filename, sep="\t"):
        try:
            logging.debug("Dumping sheet to %s..." % filename)
            self.get_df().to_csv(filename, sep=sep, header=True)
        except Exception as e:
            logging.error("Failed to dump gsheet to csv with filename: %s...\n%s" % (filename, e))


    def init_header(self, header):
        try:
            if not self.header:
                self._insert_header(header)
            elif self.header != header:
                logging.warning(
                    "Expected header differs from gsheet header!\n expected (len=%d): %s\n gsheet (len=%d): %s"
                    % (len(header), header, len(self.sheet.header), self.sheet.header)
                )
        except Exception as e:
            logging.error("Failed to set gsheet header: %s...\n%s" % (self.name, e))


class StatusServer:
    def __init__(self, json_path, port=8335):
        self.json_path = json_path
        self.port = port
        self.host = '0.0.0.0'
        self.start_json_server()

    def start_json_server(self):
        def handler_from(directory):
            def _init(self, *args, **kwargs):
                return http.server.SimpleHTTPRequestHandler.__init__(self, *args, directory=self.directory, **kwargs)
            return type(f'HandlerFrom<{directory}>',
                        (http.server.SimpleHTTPRequestHandler,),
                        {'__init__': _init, 'directory': directory})
        try:
            server = http.server.HTTPServer(
                server_address=(self.host, self.port),
                RequestHandlerClass=handler_from(self.json_path)
            )
            thread = threading.Thread(target = server.serve_forever)
            thread.daemon = True
            thread.start()
            logging.debug('Starting server at http://%s:%d on thread: %s' % (self.host , self.port, thread))
        except Exception as e:
            logging.error("Failed to set up server on port %d...\n%s" % (self.port, e))


    def write(self, status_filename, status_dict):
        json_str = json.dumps(status_dict, sort_keys=True, indent=2)
        with open(os.path.join(self.json_path, status_filename), 'w') as f:
            f.write(json_str)


class TsvLogger:
    def __init__(self, log_filename, header):
        self.file = log_filename
        self.n_cols = len(header)
        self.header = header
        self.init_log()

    def init_log(self):
        if not os.path.exists(self.file):
            logging.debug("Log file doesnt exist, creating it...")
            self.append_row(self.header)
        else:
            logging.debug("Appending to existing logfile %s..." % self.file)

    def append_row(self, row):
        if len(row) != self.n_cols:
            raise ValueError("row of length %d != %d n_cols" % (len(row), self.n_cols))
        row_str = "\t".join([str(t) for t in row])
        logging.debug("Logging to file:\n%s" % row_str)
        with open(self.file, "a") as f:
            f.write(row_str + "\n")
