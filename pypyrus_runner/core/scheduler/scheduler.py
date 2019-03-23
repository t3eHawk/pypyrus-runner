import os
import re
import sys
import time
import signal
import datetime
import pypyrus_logbook as logbook

from .trigger import Trigger
from ..operator import Operator
from ..config import Config
from ..database import Database

class Scheduler():
    """Class describing the scheduler and its API."""
    def __init__(
        self, name=None, desc=None, config=None, showtime=None, showdelay=None
    ):
        # Move to root directory.
        home = os.getenv('PYPYRUS_RUNNER_HOME')
        self._root = home or os.path.abspath(os.path.dirname(sys.argv[0]))
        os.chdir(self._root)

        # Parse configuration.
        self.config = Config(self, custom=config)
        CFG_SCHEDULER = self.config['SCHEDULER']
        CFG_DEBUG = self.config['DEBUG']
        CFG_LOG = self.config['LOG']
        CFG_ERROR = self.config['ERROR']

        # Name and description.
        self.name = name or CFG_SCHEDULER.get('name')
        self.desc = desc or CFG_SCHEDULER.get('desc')

        # Initialize log object using some parameters.
        self.log = logbook.Logger(
            self.name, desc=self.desc,
            file=CFG_LOG.getboolean('file'),
            console=CFG_LOG.getboolean('console'),
            limit_by_day=CFG_LOG.getboolean('limit_by_day'),
            limit_by_size=CFG_LOG.getboolean('limit_by_size'),
            max_size=CFG_LOG.getint('max_size'),
            err_formatting=CFG_ERROR.getboolean('formatting'),
            alarming=CFG_ERROR.getboolean('alarming'),
            debug=CFG_ERROR.getboolean('debug'))

        self._start_timestmap = None
        self._end_timestamp = None
        self._pid = self.log.sysinfo.stat.pid
        self.showtime = showtime or CFG_DEBUG.getboolean('showtime')
        self.showdelay = showdelay or CFG_DEBUG.getboolean('showdelay')

        self._operator = Operator(self)
        self._database = Database(self)
        self._trigger = Trigger(self)
        pass

    def start(self):
        """Launch the scheduler."""
        self.log
        self.log.head()
        self._checkin()
        self._sked()
        self._sync_time()
        self.log.info(f'Scheduler <{self.name}> started at PID <{self._pid}>.')

        # Iterate scheduler process.
        while True:
            self._process()
        pass

    def stop(self):
        """Stop the scheduler."""
        try:
            select = self._database.status.select()
            result = self._database.connection.execute(select).first()
            pid = result['pid']
            os.kill(pid, signal.SIGINT)
        except OSError:
            self.log.warning(f'Scheduler at PID <{pid}> already closed.')
        except:
            self.log.error()
        else:
            update = self._database.status.update().\
                values(end_timestamp=datetime.datetime.now()).\
                where(self._database.status.c.pid == pid)
            self._database.connection.execute(update)
            self.log.info(f'Scheduler at PID <{pid}> stopped.')
        pass

    def restart(self):
        self.stop()
        self.start()
        pass

    def _checkin(self):
        delete = self._database.audit.delete()
        self._database.connection.execute(delete)
        delete = self._database.status.delete()
        self._database.connection.execute(delete)
        self._start_timestmap = datetime.datetime.now()
        insert = self._database.status.insert().values(
            start_timestamp=self._start_timestmap, pid=self._pid)
        self._database.connection.execute(insert)
        signal.signal(signal.SIGINT, self._checkout)
        pass

    def _checkout(self, *args):
        self._end_timestamp = datetime.datetime.now()
        update = self._database.status.update().\
            values(end_timestamp=self._end_timestamp).\
            where(self._database.status.c.pid == self._pid)
        self._database.connection.execute(update)
        self.log.info(f'Scheduler <{self.name}> at PID <{self._pid}> stopped.')
        exit(1)
        pass

    def _sked(self):
        select = self._database.schedule.select()
        result = self._database.connection.execute(select)
        self.schedule = list(map(lambda row: dict(row), result))
        pass

    def _debug(self):
        # Log current moment if it is needed.
        if self.showtime is True:
            ticktock = 'TICK' if int(self._moment) % 2 == 0 else 'TOCK'
            self.log.debug(ticktock)
        # Log current delay if it is needed.
        if self.showdelay is True:
            self.log.debug(f'DELAY {self._delay:0.5f}')
        pass

    def _review(self):
        if self._database.modified is True:
            self._sked()
            self.log.info('SCHEDULE WAS UPDATED!')
        pass

    def _scan(self):
        now = time.localtime(self._moment)
        charge = self._trigger.charge
        pull = self._trigger.pull
        for job in self.schedule:
            if job['status'] == 'Y':
                if charge(job['month_day'], now.tm_mday) is True:
                    if charge(job['week_day'], now.tm_wday) is True:
                        if charge(job['hour'], now.tm_hour) is True:
                            if charge(job['minute'], now.tm_min) is True:
                                if charge(job['second'], now.tm_sec) is True:
                                    pull(job)

    def _active(self):
        self._debug()
        # Check that schedule was not modified.
        self._review()
        # Find jobs that must be launched at current moment.
        self._scan()
        pass

    def _passive(self):
        # Increment moment. Sleep till the next step.
        self._move_time()
        pass

    def _process(self):
        """
        Basic scheduler process.
        All actions that must be done during one scheduler step.
        """
        # Active phase.
        self._active()
        # Passive phase.
        self._passive()
        pass

    def _sync_time(self):
        """Set current scheduler moment."""
        self._delay = 0
        self._moment = time.time()
        self.log.info('TIME WAS SYNCHRONIZED')
        pass

    def _move_time(self):
        delay = time.time() - self._moment
        wait = 1.0 - delay
        try:
            time.sleep(wait)
        except ValueError:
            self.log.warning('TIME IS BROKEN!')
            self._sync_time()
        else:
            self._moment += 1
        finally:
            self._delay = delay
        pass

    @property
    def root(self):
        return self._root

    @property
    def pid(self):
        return self._pid

    @property
    def moment(self):
        """Current scheduler moment"""
        return self._moment

    @property
    def delay(self):
        """Current scheduler delay"""
        return self._delay

    @property
    def start_timestamp(self):
        return self._start_timestamp

    @property
    def end_timestamp(self):
        return self._end_timestamp
