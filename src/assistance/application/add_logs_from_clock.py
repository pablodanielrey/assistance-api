
import logging
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
        return self.buffer.find(log) is not None


    def __next__(self) -> AttLog:
        """Returns the logs that are in the source but not in the buffer.  
        It adds the log to the buffer upon returning it.
        TODO: Make more efficient the saving to the buffer without using a generator.
        """
        assert self.logs_iterator is not None
        log = None
        while not log:
            try:
                log = self.logs_iterator.__next__()
            except StopIteration as st:
                logging.debug(f"fin del source")
                raise st
            logging.debug(f"Log que viene de source : {log}")
            if self._find_log_in_buffer(log):
                log = None
            else:
                logging.debug(f"Salvando log {log}")
                self.buffer.save((l for l in [log]))
                logging.debug(f"Retornando log {log}")
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
        logging.debug("Generando repo de google")
        repo = self.repos.create(parent=self.parent)

        # logs = self.clock.get()
        logging.debug("Generando iterador de buffer")
        iterator = self._get_buffer_iterator()

        logging.debug("Salvando los logs en google")
        repo.save(iterator)
        
