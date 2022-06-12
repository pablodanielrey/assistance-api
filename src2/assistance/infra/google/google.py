
from __future__ import print_function

import datetime
from mimetypes import MimeTypes
import os.path
from syslog import LOG_DEBUG

from pydantic import BaseSettings

from google.oauth2 import service_account
from googleapiclient.discovery import build


class GoogleSettings(BaseSettings):
    user: str = 'sistemas@econo.unlp.edu.ar'
    credentials_file: str = 'credentials/credentials.json'


class Credentials:

    def __init__(self, settings: GoogleSettings):
        self.config = settings

    def get_credentials(self):
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            # 'https://www.googleapis.com/auth/drive.metadata.readonly',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = service_account.Credentials.from_service_account_file(self.config.credentials_file, scopes=SCOPES)
        credentials = creds.with_subject(self.config.user)

        return credentials    
