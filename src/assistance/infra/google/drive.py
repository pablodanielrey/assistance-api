
import logging
from typing import Protocol
import redis


from googleapiclient.discovery import build

from .protocol import Command
from .google import Credentials
from .settings import GoogleSettings


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


class CachedDriveResource(DriveResource):

    REDIS_KEY = "google"

    def __init__(self, drive: Drive):
        super().__init__(drive)
        self.conf = GoogleSettings()
        self.redis = redis.Redis(host=self.conf.google_redis_host, port=self.conf.google_redis_port, db=self.conf.google_redis_db)


    def get_file_id(self, parent_id: str, name: str) -> str:
        key = f"file_id_{parent_id}_{name}"
        fid = self.redis.hget(self.REDIS_KEY, key)
        if fid:
            return fid.decode('utf8')

        fid = super().get_file_id(parent_id, name)

        self.redis.hset(self.REDIS_KEY, key, fid.encode('utf8'))
        return fid

    def get_folder_id(self, name: str) -> str:
        key = f"folder_id_{name}"
        fid = self.redis.hget(self.REDIS_KEY, key)
        if fid:
            return fid.decode('utf8')

        fid = super().get_folder_id(name)
        self.redis.hset(self.REDIS_KEY, key, fid.encode('utf8'))
        return fid


    def create_file(self, parent_id: str, name: str) -> str:
        fid = super().create_file(parent_id, name)

        key = f"file_id_{parent_id}_{name}"
        self.redis.hset(self.REDIS_KEY, key, fid.encode('utf8'))
        return fid
