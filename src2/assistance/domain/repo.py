from typing import Protocol
from .entities import AttLog

class AttLogRepo(Protocol):

    def save(self, logs: list[AttLog]):
        ...


class RepoFactory(Protocol):
    def create(self, parent: str, name: str) -> AttLogRepo:
        ...


class AttLogClock(Protocol):

    def get(self) -> list[AttLog]:
        ...