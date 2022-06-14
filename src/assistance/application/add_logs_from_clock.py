
import datetime
from typing import Iterator

from ..domain.entities import AttLog
from ..domain.repo import AttLogRepo, RepoFactory


class BufferIterator(Iterator):
    """Filter the logs from the source and only return the logs that are not in the buffer.  
    It adds the logs to the buffer upon returning it.
    """

    def __init__(self, source: AttLogRepo, buffer: AttLogRepo):
        self.source = source
        self.logs_iterator = None
        self.buffer = buffer
     

    def __iter__(self) -> Iterator[AttLog]:
        self.logs_iterator = self.source.get()
        return self

    def _find_log_in_buffer(self, log: AttLog) -> bool:
        return False


    def __next__(self) -> AttLog:
        """Returns the logs that are in the source but not in the buffer.  
        It adds the log to the buffer upon returning it.
        TODO: Make more efficient the saving to the buffer without using a generator.
        """
        assert self.logs_iterator is not None
        log = None
        while not log:
            log = self.logs_iterator.__next__()
            if not self._find_log_in_buffer(log):
                self.buffer.save((l for l in [log]))
                return log
        raise StopIteration()


class AddLogsFromClock:
    """
    Get's the logs from assistance zksoftware clock and publish them onto a shared spreadsheet
    """
    def __init__(self, source: AttLogRepo, buffer: AttLogRepo, destiny: RepoFactory):
        self.repos = destiny
        self.clock = source
        self.buffer = buffer
        self.parent = 'attendance_logs'


    def _get_buffer_iterator(self):
        return BufferIterator(self.clock, self.buffer)

    def execute(self):
        repo = self.repos.create(parent=self.parent)

        # logs = self.clock.get()
        iterator = self._get_buffer_iterator()
        repo.save(iterator)
        
