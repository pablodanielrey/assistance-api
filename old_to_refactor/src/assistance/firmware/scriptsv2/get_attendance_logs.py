import logging
import sys
import datetime
from zk import ZK, const
from pydantic import BaseModel, validator


class AttLog(BaseModel):
    uid: int
    user_id: str
    timestamp: datetime.datetime
    status: int
    punch: int

    @validator('timestamp', pre=True)
    def timestamp_conversion(cls, t):
        print(type(t))
        return t

    class Config:
        orm_mode = True


if __name__ == '__main__':
    ip = sys.argv[1]
    file = sys.argv[2]

    conn = None
    zk = ZK(ip, port=4370, timeout=5)
    print('Connecting to device ...')
    conn = zk.connect()
    try:
        conn.enable_device()
        print('Firmware Version: : {}'.format(conn.get_firmware_version()))
        conn.test_voice()

        logs = conn.get_attendance()
        for log in logs:
            att_log = AttLog.from_orm(log)
            print(att_log.json())

        conn.enable_device()

    except Exception as e2:
        logging.exception(e2)
        conn.disconnect()
