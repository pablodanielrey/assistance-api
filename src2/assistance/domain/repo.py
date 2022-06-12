from typing import Protocol, Iterator
from .entities import AttLog

class AttLogRepo(Protocol):

    def save(self, logs: Iterator[AttLog]):
        ...


class RepoFactory(Protocol):
    def create(self, parent: str, name: str) -> AttLogRepo:
        ...


class AttLogClock(Protocol):

    def get(self) -> Iterator[AttLog]:
        ...