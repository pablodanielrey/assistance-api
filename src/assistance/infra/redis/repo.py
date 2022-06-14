
from typing import Iterator, Optional
import redis

from ...domain.entities import AttLog
from ...domain.repo import AttLogRepo

from .settings import RedisSettings

class RedisRepo(AttLogRepo):

    def __init__(self):
        self.conf = RedisSettings()
        self.db = redis.Redis(host=self.conf.redis_host, port=self.conf.redis_port, db=self.conf.redis_db)

    def _get_log_uid(self, log: AttLog) -> str:
        return ""

    def save(self, logs: Iterator[AttLog]):
        for log in logs:
            pipe = self.db.pipeline()
            lid = self._get_log_uid(log)
            pipe.hmset(name=lid, log.dict())  # type: ignore
            pipe.execute(raise_on_error=True)

    def get(self) -> Iterator[AttLog]:
        raise NotImplementedError()

    def find(self, log: AttLog) -> Optional[AttLog]:
        lid = self._get_log_uid(log)
        if not self.db.exists(lid):
            return None
        logs_data = self.db.hgetall(lid)
        return AttLog.parse_obj(logs_data)
