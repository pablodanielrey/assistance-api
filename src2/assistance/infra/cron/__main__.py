import logging
import datetime

from typing import Iterator

from ...application.add_logs_from_clock import AddLogsFromClock
from ..google import GoogleDriveFactory
from ..zksoftware import ZkSoftwareClock

from ...domain.entities import AttLog
from ...domain.repo import AttLogClock

from .settings import CronSettings
import random


def execute_crons():
    google = GoogleDriveFactory()
    clock = ZkSoftwareClock()
    add_logs_from_clock = AddLogsFromClock(repos=google, clock=clock)
    add_logs_from_clock.execute()



config = CronSettings()
logging.basicConfig(level=config.log_level, format=config.log_format)


execute_crons()
