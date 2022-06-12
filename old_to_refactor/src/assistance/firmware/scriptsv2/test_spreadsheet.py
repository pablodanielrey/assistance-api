
from __future__ import print_function

import datetime
from mimetypes import MimeTypes
import os.path
from syslog import LOG_DEBUG

from google.oauth2 import service_account
from googleapiclient.discovery import build

import logging
logging.basicConfig(level=logging.DEBUG)

def get_attlogs_folder_id(drive) -> str:
    page_token = None
    items = []
    while True:
        results = drive.files().list(q="mimeType='application/vnd.google-apps.folder' and name contains 'attendance_logs'",
                                    spaces='drive',
                                    fields="nextPageToken, files(id, name)",
                                    pageSize=10,
                                    pageToken=page_token).execute()
        items.extend(results.get('files', []))
        page_token = results.get('nextPageToken', None)
        if not page_token:
            break

    if not items or len(items) == 0:
        raise Exception('no se encuentra la carpeta de los logs')
    return items[0]['id']


def get_attlog_file_name() -> str:
    sname = f"logs_{datetime.datetime.now().date()}"
    return sname

def get_attlog_file(drive, parent_id: str) -> str:

    sname = get_attlog_file_name()

    page_token = None
    items = []
    while True:
        results = drive.files().list(q=f"mimeType='application/vnd.google-apps.spreadsheet' and trashed = false and name = '{sname}' and '{parent_id}' in parents",
                                    spaces='drive',
                                    fields="nextPageToken, files(id, name, parents)",
                                    pageSize=10,
                                    pageToken=page_token).execute()
        items.extend(results.get('files', []))
        page_token = results.get('nextPageToken', None)
        if not page_token:
            break

    if not items or len(items) == 0:
        raise Exception('no se encuentra el archivo de logs')
    
    logging.debug(items)
    return items[0]['id']


def create_attlog_file(drive, parent_id: str) -> str:
    sname = get_attlog_file_name()

    attlogs_folter_id = parent_id
    meta = {
        'mimeType': "application/vnd.google-apps.spreadsheet", 
        'parents': [attlogs_folter_id],
        'name': sname
    }
    data = drive.files().create(body=meta,fields='id, name, parents, mimeType').execute()
    logging.debug(data)
    return data['id']


    
def get_credentials():
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        # 'https://www.googleapis.com/auth/drive.metadata.readonly',
        'https://www.googleapis.com/auth/drive'
    ]
    SERVICE_ACCOUNT_FILE = 'credentials/credentials.json'


    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    credentials = creds.with_subject('sistemas@econo.unlp.edu.ar')

    return credentials


def add_log_to_file(sheets, sid:str):
    now = datetime.datetime.now()
    body = {
        'values':  [[str(now.date()),str(now.time().replace(microsecond=0)),'27294557'] for _ in range(0,10)]
    }
    sheets.spreadsheets().values().append(spreadsheetId=sid,
                             range="A:D",
                             valueInputOption="USER_ENTERED",
                             insertDataOption="INSERT_ROWS",
                             body=body).execute()


if __name__ == '__main__':

    credentials = get_credentials()
    sheets = build('sheets', 'v4', credentials=credentials)
    drive = build('drive', 'v3', credentials=credentials)

    folder_id = get_attlogs_folder_id(drive)
    try:
        sid = get_attlog_file(drive, folder_id)
    except Exception as e:
        sid = create_attlog_file(drive, folder_id)


    add_log_to_file(sheets, sid)
    print(sid)



