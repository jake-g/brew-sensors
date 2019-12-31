#!/usr/bin/python
from __future__ import print_function

import gspread
import logging
import os
import pandas
from oauth2client.service_account import ServiceAccountCredentials


class gSheetLogger:
    def __init__(self, key_file, gsheet_name, sheet_idx=0, header=[]):
        self.name = gsheet_name
        self.sheet_idx = sheet_idx
        self.service_email = ''
        self.sheet = None
        self.header = None
        self.client = None
        self._authorize_client(key_file)
        self._get_sheet()
        if header: self.init_header(header)

    def _authorize_client(self, key_file,
                          scope=('https://spreadsheets.google.com/feeds',
                                 'https://www.googleapis.com/auth/drive')
                          ):
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(key_file, scope)
            self.service_email = str(creds.service_account_email)
            self.client = gspread.authorize(creds)
        except Exception as e:
            logging.error('%s\nFailed to authenticate client...' % e)

    def _get_sheet(self):
        try:
            self.sheet = self.client.open(self.name).get_worksheet(self.sheet_idx)
            logging.debug('Sheet Values:\n%s' % self.sheet.get_all_values())
        except Exception as e:
            logging.error('%s\nEnsure files are shared with this email:\n\n  %s' % (e, self.service_email))
        self._set_header()

    def _set_header(self):
        _header = self.sheet.row_values(1)  # i guess header starts at row 1
        if _header:
            self.header = _header
        else:
            logging.warning('Sheet has no header data!')

    def _insert_header(self, header):
        self.sheet.insert_row(header, 1)
        self._set_header()

    def get_df(self):
        self._set_header()
        return pandas.DataFrame(self.sheet.get_all_records(),
                                columns=self.header)

    def dump_sheet(self, filename, sep='\t'):
        logging.debug('Dumping sheet to %s...' % filename)
        self.get_df().to_csv(filename, sep=sep, header=True)

    def init_header(self, header):
        try:
            if not self.header:
                self._insert_header(header)
            elif self.header != header:
                logging.warning(
                    'Expected header differs from gsheet header!\n expected (len=%d): %s\n gsheet (len=%d): %s' % (
                        len(header), header, len(self.sheet.header), self.sheet.header))
        except Exception as e:
            logging.error('Failed to set gsheet header: %s...\n%s' % (self.name, e))


class TsvLogger:
    def __init__(self, log_filename, header):
        self.file = log_filename
        self.n_cols = len(header)
        self.header = header
        self.init_log()

    def init_log(self):
        if not os.path.exists(self.file):
            logging.debug('Log file doesnt exist, creating it...')
            self.append_row(self.header)
        else:
            logging.debug('Appending to existing logfile %s...' % self.file)

    def append_row(self, row):
        if len(row) != self.n_cols:
            raise ValueError('row of length %d != %d n_cols' % (len(row), self.n_cols))
        row_str = '\t'.join([str(t) for t in row])
        logging.debug('Logging to file:\n%s' % row_str)
        with open(self.file, 'a') as f:
            f.write(row_str + '\n')
