
from __future__ import print_function

import datetime
from mimetypes import MimeTypes
import os.path
from syslog import LOG_DEBUG

from google.oauth2 import service_account
from googleapiclient.discovery import build

from typing import Any, Iterator


from assistance.domain.entities import AttLog

from .google import Credentials


class Spreadsheet:

    def __init__(self, credentials : Credentials):
        self.credentials = credentials
        self.sheets = build('sheets', 'v4', credentials=self.credentials.get_credentials())


    def add_recods(self, spreadsheet_id: str, records: Iterator[AttLog]):
        body = {
            'values':  [
                [str(log.date), str(log.time.replace(microsecond=0)), log.dni] 
                for log in records
            ]
        }
        self.sheets.spreadsheets().values().append(spreadsheetId=spreadsheet_id,
                                range="A:D",
                                valueInputOption="USER_ENTERED",
                                insertDataOption="INSERT_ROWS",
                                body=body).execute()

