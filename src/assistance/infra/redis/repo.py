
from typing import Iterator, Optional
import redis
import json
import logging

from ...domain.entities import AttLog
from ...domain.repo import AttLogRepo

from .settings import RedisSettings

class RedisRepo(AttLogRepo):

    def __init__(self):
        self.conf = RedisSettings()
        self.db = redis.Redis(host=self.conf.redis_host, port=self.conf.redis_port, db=self.conf.redis_db)

    def _get_log_uid(self, log: AttLog) -> str:
        return f"{log.dni}_{log.date}_{log.time}"

    def save(self, logs: Iterator[AttLog]):
        for log in logs:
            pipe = self.db.pipeline()
            lid = self._get_log_uid(log)

            l_data = json.dumps(log.json())

            pipe.hset(name=lid, key='data', value=l_data)  # type: ignore
            pipe.execute(raise_on_error=True)

    def get(self) -> Iterator[AttLog]:
        raise NotImplementedError()

    def find(self, log: AttLog) -> Optional[AttLog]:
        lid = self._get_log_uid(log)
        if not self.db.exists(lid):
            return None
        # logs_data = self.db.hgetall(lid)
        # return AttLog.parse_obj(logs_data)
        r_data = self.db.hget(name=lid, key='data')
        assert r_data is not None
        jdata = json.loads(r_data.decode('utf8'))
        logging.debug(f"deserializing : {jdata}")
        return AttLog.parse_raw(jdata)
