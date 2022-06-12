import logging
import datetime

from typing import Iterator

from ...application.add_logs_from_clock import AddLogsFromClock
from ..google import GoogleDriveFactory, GoogleRepo

from ...domain.entities import AttLog
from ...domain.repo import AttLogClock

from .settings import CronSettings
import random

class ExampleLogs(AttLogClock):

    def get(self) -> Iterator[AttLog]:
        return (AttLog(date=(datetime.datetime.now() + datetime.timedelta(days=random.randint(1,2))).date(), time=datetime.datetime.now().time(), dni='27294557') for _ in range(0,10))


def execute_crons():
    google = GoogleDriveFactory()
    clock = ExampleLogs()
    add_logs_from_clock = AddLogsFromClock(repos=google, clock=clock)
    add_logs_from_clock.execute()



config = CronSettings()
logging.basicConfig(level=config.log_level, format=config.log_format)


execute_crons()
