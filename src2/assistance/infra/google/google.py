
from __future__ import print_function
import logging

import datetime
from mimetypes import MimeTypes
import os.path
from syslog import LOG_DEBUG

from pydantic import BaseSettings

from google.oauth2 import service_account
from googleapiclient.discovery import build

from .settings import GoogleSettings

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
        credentials = creds.with_subject(self.config.google_user)
        return credentials    
