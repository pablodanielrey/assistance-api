
import datetime

from ..domain.repo import AttLogClock, RepoFactory



class AddLogsFromClock:
    """
    Get's the logs from assistance zksoftware clock and publish them onto a shared spreadsheet
    """
    def __init__(self, repos: RepoFactory, clock: AttLogClock):
        self.repos = repos
        self.clock = clock
        self.parent = 'attendance_logs'

    def _get_attlog_file_name(self) -> str:
        sname = f"logs_{datetime.datetime.now().date()}"
        return sname

    def execute(self):
        name = self._get_attlog_file_name()
        repo = self.repos.create(parent=self.parent)

        logs = self.clock.get()
        repo.save(logs)
        
