import logging

from ...application.add_logs_from_clock import AddLogsFromClock
from ..google import GoogleDriveFactory, GoogleRepo
from ...domain.repo import AttLogClock

from .settings import CronSettings

class ExampleLogs(AttLogClock):

    def get(self) -> list[AttLogClock]:
        ...


def execute_crons():
    google = GoogleDriveFactory()
    clock = ExampleLogs()
    add_logs_from_clock = AddLogsFromClock(repos=google, clock=clock)
    add_logs_from_clock.execute()



config = CronSettings()
logging.basicConfig(level=config.log_level, format=config.log_format)


execute_crons()
