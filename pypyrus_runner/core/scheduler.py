import datetime as dt
import os
import re
import pypyrus_logbook as logbook
import signal
import sys
import time

from .conf import read_config
from .db import Database
from .operator import Operator
from .utils import get_root, join_persons


class Scheduler():
    """Class describing the scheduler and its API."""

    def __init__(self, name=None, desc=None, config=None,
                 showtime=None, showdelay=None):
        # Parse configuration.
        self.root = get_root()
        self.config = read_config(config)
        self.__database = Database()
        self.__operator = Operator(config=self.config)

        owner = self.config.read_one_from_general('owner')
        recipients = self.config.read_one_from_logger('smtp.recipients')
        self._persons = join_persons(owner, recipients)

        # Name and description.
        SCHEDULER = self.config.scheduler
        self.name = name or SCHEDULER.get('name')
        self.desc = desc or SCHEDULER.get('desc')
        self.showtime = showtime or SCHEDULER.getboolean('showtime')
        self.showdelay = showdelay or SCHEDULER.getboolean('showdelay')

        params = self.config.read_all_from_logger()
        params['smtp']['recipients'] = self._persons
        self.log = logbook.getlogger(app=self.name, desc=self.desc, **params)

        self._pid = self.log.sysinfo.desc.pid
        self._delay = None
        self._moment = None
        self._start_date = None
        self._end_date = None
        pass

    @property
    def pid(self):
        """PID that reflects the scheduler."""
        return self._pid

    @property
    def moment(self):
        """Current scheduler moment."""
        return self._moment

    @property
    def delay(self):
        """Current scheduler delay."""
        return self._delay

    @property
    def start_date(self):
        """Time when scheduler started."""
        return self._start_date

    @property
    def end_date(self):
        """Time when scheduler stopped."""
        return self._end_date

    @property
    def persons(self):
        return self._persons

    def start(self):
        """Launch the scheduler."""
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
            select = self.__database.status.select()
            result = self.__database.connection.execute(select).first()
            pid = result['pid']
            os.kill(pid, signal.SIGINT)
        except OSError:
            self.log.warning(f'Scheduler at PID <{pid}> already closed.')
        except:
            self.log.error()
        else:
            update = self.__database.status.update().\
                values(end_date=dt.datetime.now()).\
                where(self.__database.status.c.pid == pid)
            self.__database.connection.execute(update)
            self.log.info(f'Scheduler at PID <{pid}> stopped.')
        pass

    def restart(self):
        self.stop()
        self.start()
        pass

    def _checkin(self):
        delete = self.__database.audit.delete()
        self.__database.connection.execute(delete)
        delete = self.__database.status.delete()
        self.__database.connection.execute(delete)
        self._start_date = dt.datetime.now()
        insert = self.__database.status.insert().\
            values(start_date=self._start_date, pid=self._pid)
        self.__database.connection.execute(insert)
        signal.signal(signal.SIGINT, self._checkout)
        pass

    def _checkout(self, *args):
        self._end_date = dt.datetime.now()
        update = self.__database.status.update().\
            values(end_date=self._end_date).\
            where(self.__database.status.c.pid == self._pid)
        self.__database.connection.execute(update)
        self.log.info(f'Scheduler <{self.name}> at PID <{self._pid}> stopped.')
        exit(1)
        pass

    def _sked(self):
        select = self.__database.schedule.select()
        result = self.__database.connection.execute(select)
        self.schedule = list(map(lambda row: dict(row), result))
        pass

    def _sync_time(self):
        """Set current scheduler moment."""
        self._delay = 0
        self._moment = time.time()
        self.log.info('TIME WAS SYNCHRONIZED')
        pass

    def _process(self):
        """Basic scheduler process.
        All actions that must be done during one scheduler step.
        """
        # Active phase.
        self._active()
        # Passive phase.
        self._passive()
        pass

    def _active(self):
        self._debug()
        # Check that schedule was not modified.
        self._review()
        # Find jobs that must be launched at current moment.
        self._trigger()
        pass

    def _debug(self):
        # Log current moment if it is needed.
        if self.showtime is True:
            ticktock = 'TICK' if int(self._moment) % 2 == 0 else 'TOCK'
            self.log.info(ticktock)
        # Log current delay if it is needed.
        if self.showdelay is True:
            self.log.info(f'DELAY {self._delay:0.5f}')
        pass

    def _review(self):
        if self.__database.modified is True:
            self._sked()
            self.log.info('SCHEDULE WAS UPDATED!')
        pass

    def _trigger(self):
        now = time.localtime(self._moment)
        for job in self.schedule:
            if (job['status'] == 'Y' and
                self._charge(job['month_day'], now.tm_mday) is True and
                self._charge(job['week_day'], now.tm_wday) is True and
                self._charge(job['hour'], now.tm_hour) is True and
                self._charge(job['minute'], now.tm_min) is True and
                self._charge(job['second'], now.tm_sec) is True):
                    self._pull(job)

    def _charge(self, unit, now):
        # Check if empty or *.
        if re.match(r'^(\*)$', unit) is not None:
            return True
        # Check if unit is lonely digit and equals to now.
        elif re.match(r'^\d+$', unit) is not None:
            unit = int(unit)
            return True if now == unit else False
        # Check if unit is a cycle and integer division with now is true.
        elif re.match(r'^/\d+$', unit) is not None:
            unit = int(re.search(r'\d+', unit).group())
            if unit == 0: return False
            return True if now % unit == 0 else False
        # Check if unit is a range and now is in this range.
        elif re.match(r'^\d+-\d+$', unit):
            unit = [int(i) for i in re.findall(r'\d+', unit)]
            return True if now in range(unit[0], unit[1] + 1) else False
        # Check if unit is a list and now is in this list.
        elif re.match(r'^\d+,\s*\d+.*$', unit):
            unit = [int(i) for i in re.findall(r'\d+', unit)]
            return True if now in unit else False
        # All other cases is not for the now.
        else:
            return False

    def _pull(self, job):
        try:
            id = job['id']
            env = job['environment']
            file = job['file']
            params = job['parameters']
            params += ' -a'
            exe = self.config.proxy['ENVIRONMENTS'].get(env)
            self.log.info(f'CREATING SUBPROCESS FOR JOB {id}...')
            # Job will run as separate process.
            self.__operator.make_process(exe, file, params)
        except:
            self.log.error(f'SUBPROCESS FOR JOB {id} WAS NOT CREATED')
            self.log.error()
        else:
            self.log.info(f'SUBPROCESS FOR JOB {id} WAS CREATED SUCCESSFULLY')
        pass

    def _passive(self):
        # Increment moment. Sleep till the next step.
        self._move_time()
        pass

    def _move_time(self):
        """Move scheduler to next moment."""
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
