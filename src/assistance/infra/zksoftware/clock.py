from typing import Iterator
import logging

from zk import ZK, const

from ...domain.repo import AttLogClock
from ...domain.entities import AttLog

from .settings import ZkSettings
from .entities import AttLog as ZkAttLog

class ZkSoftwareClock(AttLogClock):

    def __init__(self):
        self.conf = ZkSettings()
        self.zk = ZK(ip=self.conf.ip, port=self.conf.port, timeout=self.conf.timeout, force_udp=self.conf.force_udp, ommit_ping=self.conf.ommit_ping, verbose=self.conf.verbose)

    def get(self) -> Iterator[AttLog]:
        """Get's the logs from the clock and maps it to a domain AttLog

        Returns:
            - Iterator of the domain attlogs
        """
        conn = self.zk.connect()
        try:
            conn.disable_device()
            try:
                logging.info('Firmware Version: : {}'.format(conn.get_firmware_version()))
                # conn.test_voice()

                logs = conn.get_attendance()
                attlogs = [ZkAttLog.from_orm(log) for log in logs]
                return (AttLog(date=l.timestamp.date(), time=l.timestamp.time().replace(microsecond=0), dni=l.user_id) for l in attlogs)
            
            finally:
                conn.enable_device()

        finally:
            conn.disconnect()