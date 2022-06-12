
import logging
from typing import Protocol

from googleapiclient.discovery import build

from .protocol import Command
from .google import Credentials


class Folder(Protocol):
    def list(self, **kw) -> Command:
        ...

    def create(self, *args, **kw) -> Command:
        ...



class Drive:
    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.drive = build('drive', 'v3', credentials=credentials.get_credentials())

    def files(self) -> Folder:
        return self.drive.files()



class DriveResource:

    def __init__(self, drive: Drive):
        self.drive = drive
        

    def get_file_id(self, parent_id: str, name: str) -> str:

        page_token = None
        items = []
        while True:
            results = self.drive.files().list(q=f"mimeType='application/vnd.google-apps.spreadsheet' and trashed = false and name = '{name}' and '{parent_id}' in parents",
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
    
    def get_folder_id(self, name: str) -> str:
        page_token = None
        items = []
        while True:
            results = self.drive.files().list(q=f"mimeType='application/vnd.google-apps.folder' and name contains '{name}'",
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

    def create_file(self, parent_id: str, name: str) -> str:
        attlogs_folter_id = parent_id
        meta = {
            'mimeType': "application/vnd.google-apps.spreadsheet", 
            'parents': [attlogs_folter_id],
            'name': name
        }
        data = self.drive.files().create(body=meta,fields='id, name, parents, mimeType').execute()
        logging.debug(data)
        return data['id']        


