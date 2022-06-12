from ...domain.repo import RepoFactory, AttLogRepo
from ...domain.entities import AttLog

from .google import GoogleSettings, Credentials
from .drive import Drive, DriveResource
from .spreadsheet import Spreadsheet


class GoogleRepo(AttLogRepo):

    def __init__(self, repo_name: str, file_name: str, drive_api: Drive, spreadsheet_api: Spreadsheet):
        self.repo_name = repo_name
        self.file_name = file_name
        self.drive_api = drive_api
        self.spreadsheet_api = spreadsheet_api

    def _get_spreadsheet_id(self):
        dr = DriveResource(self.drive_api)
        folder_id = dr.get_folder_id(self.repo_name)
        try:
            file_id = dr.get_file_id(folder_id, self.file_name)
        except Exception as e:
            file_id = dr.create_file(self.repo_name, self.file_name)
        return file_id

    def save(self, logs: list[AttLog]):
        sid = self._get_spreadsheet_id()
        self.spreadsheet_api.add_recods(sid, logs)


class GoogleDriveFactory(RepoFactory):

    def __init__(self):
        self.config = GoogleSettings()
        self.credentials = Credentials(self.config)
        self.drive_api = Drive(credentials=self.credentials)
        self.spreadsheet_api = Spreadsheet(credentials=self.credentials)

    def create(self, parent: str, name: str) -> GoogleRepo:
        return GoogleRepo(parent, name, self.drive_api, self.spreadsheet_api)
