from typing import Iterator, Optional
import logging

from zk import ZK, const

from ...domain.repo import AttLogRepo
from ...domain.entities import AttLog

from .settings import ZkSettings
from .entities import AttLog as ZkAttLog

class ZkSoftwareClock(AttLogRepo):

    def __init__(self):
        self.conf = ZkSettings()
        logging.debug(self.conf.dict())
        self.zk = ZK(ip=self.conf.ip, port=self.conf.port, timeout=self.conf.timeout, force_udp=self.conf.force_udp, ommit_ping=self.conf.ommit_ping, verbose=False)
        # self.zk = ZK(ip="172.25.0.70", port=4370, timeout=5, force_udp=False, ommit_ping=True, verbose=True)

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

    def save(self, logs: Iterator[AttLog]):
        raise NotImplementedError()

    def find(self, log: AttLog) -> Optional[AttLog]:
        raise NotImplementedError()