
from typing import Iterator, Protocol, Any

class Result(Protocol):
    def get(self, *args, **kw) -> Iterator:
        ...

    def __getitem__(self, *args, **kw) -> Any:
        ...


class Command(Protocol):
    def execute(self) -> Result:
        ...



