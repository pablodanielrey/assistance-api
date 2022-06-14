from typing import Protocol, Iterator, Optional
from .entities import AttLog

class AttLogRepo(Protocol):

    def save(self, logs: Iterator[AttLog]):
        ...

    def get(self) -> Iterator[AttLog]:
        ...

    def find(self, lid: str) -> Optional[AttLog]:
        ...

class RepoFactory(Protocol):
    def create(self, parent: str) -> AttLogRepo:
        ...
