import logging
from typing import Iterator, Optional

from ...domain.repo import RepoFactory, AttLogRepo
from ...domain.entities import AttLog

from .google import GoogleSettings, Credentials
from .drive import Drive, DriveResource, CachedDriveResource
from .spreadsheet import Spreadsheet


class MockedGoogleRepo(AttLogRepo):

    def save(self, logs: Iterator[AttLog]):
        for log in logs:
            logging.debug(f"salvando -> {log}")

    def get(self) -> Iterator[AttLog]:
        raise NotImplementedError()

    def find(self, log: AttLog) -> Optional[AttLog]:
        raise NotImplementedError()


class GoogleRepo(AttLogRepo):

    def __init__(self, repo_name: str, drive_api: Drive, spreadsheet_api: Spreadsheet):
        self.repo_name = repo_name
        self.drive_api = drive_api
        self.spreadsheet_api = spreadsheet_api

    def _get_spreadsheet_id(self, name: str):
        dr = CachedDriveResource(self.drive_api)
        drive_folder_id = dr.get_folder_id(self.repo_name)
        try:
            file_id = dr.get_file_id(drive_folder_id, name)
        except Exception as e:
            file_id = dr.create_file(drive_folder_id, name)
        return file_id
    

    def _map_for_date(self, logs: Iterator[AttLog]) -> dict[str, list[AttLog]]:
        """
        Returns a map with dates as keys and a list of AttLogs corresponding to that date.
        """
        data = {}
        for log in logs:
            key = str(log.date)
            if key not in data:
                data[key] = []
            data[key].append(log)
        return data

    def save(self, logs: Iterator[AttLog]):
        keyed_data = self._map_for_date(logs)
        for date, dlogs in keyed_data.items():
            sid = self._get_spreadsheet_id(f"logs_{date}")
            self.spreadsheet_api.add_recods(sid, (l for l in dlogs))

    def get(self) -> Iterator[AttLog]:
        raise NotImplementedError()

    def find(self, log: AttLog) -> Optional[AttLog]:
        raise NotImplementedError()


class GoogleDriveFactory(RepoFactory):

    def __init__(self):
        self.config = GoogleSettings()
        if self.config.google_repo != "MOCK":
            self.credentials = Credentials(self.config)
            self.drive_api = Drive(credentials=self.credentials)
            self.spreadsheet_api = Spreadsheet(credentials=self.credentials)

    def create(self, parent: str) -> AttLogRepo:
        if self.config.google_repo == "MOCK":
            return MockedGoogleRepo()
        return GoogleRepo(parent, self.drive_api, self.spreadsheet_api)
        
