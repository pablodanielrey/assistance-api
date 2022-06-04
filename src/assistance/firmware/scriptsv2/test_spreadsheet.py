
from __future__ import print_function

import datetime
import os.path

from google.oauth2 import service_account
from google.auth import impersonated_credentials
from googleapiclient.discovery import build


SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]
SERVICE_ACCOUNT_FILE = 'credentials/credentials.json'

creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
credentials = impersonated_credentials.Credentials(
    source_credentials=creds,
    target_principal='sistemas@econo.unlp.edu.ar',
    target_scopes=SCOPES,
    lifetime=500)

try:
    service = build('sheets', 'v4', credentials=credentials)
    drive = build('drive', 'v3', credentials=credentials)

    # Call the Drive v3 API
    results = drive.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    print('Files:')
    for item in items:
        print(u'{0} ({1})'.format(item['name'], item['id']))

except Exception as error:
    # TODO(developer) - Handle errors from drive API.
    print(f'An error occurred: {error}')


