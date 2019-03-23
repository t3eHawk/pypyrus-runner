import os
import re
import sys
import atexit
import sqlalchemy as sql

import pypyrus_logbook as logbook

from datetime import datetime

from .config import Config as JobConfig
from ..config import Config
from ..database import Database

class Job():
    def __init__(self, name=None, desc=None, config=None, persons=None):
        # Move to job directory.
        file = os.path.abspath(sys.argv[0])
        folder = os.path.abspath(os.path.dirname(file))
        home = os.getenv('PYPYRUS_RUNNER_HOME')
        root = home or os.path.abspath(f'{folder}/../../')
        os.chdir(folder)

        self._file = file
        self._root = root

        # Parse configuration objects.
        self.config = Config(self)
        self.job_config = JobConfig(self, custom=config)

        self._database = Database(self)
        self.details = self._select_details()
        self._id = self.details['id']
        self.name = self.details['name']
        self.desc = self.details['description']

        # Emails for information and notifications.
        owner = self.config['MANAGER'].get('owner')
        persons = persons or self.job_config['JOB'].get('persons')
        self._persons = []
        if owner is not None:
            self._persons.extend(owner.split())
        if persons is not None:
            self._persons.extend(persons.split())

        self.log = logbook.Logger(
            self.name, desc=self.desc,
            console=self.job_config['LOG'].getboolean('console'),
            limit_by_day=self.job_config['LOG'].getboolean('limit_by_day'),
            limit_by_size=self.job_config['LOG'].getboolean('limit_by_size'),
            max_size=self.job_config['LOG'].getint('max_size'),
            err_formatting=self.job_config['ERROR'].getboolean('formatting'),
            alarming=self.job_config['ERROR'].getboolean('alarming'),
            email=self.config['EMAIL'].get('address'),
            ip=self.config['EMAIL'].get('ip'),
            port=self.config['EMAIL'].get('port'),
            user=self.config['EMAIL'].get('user'),
            password=self.config['EMAIL'].get('password'),
            tls=self.config['EMAIL'].getboolean('tls'),
            recipients=self._persons)

        self.log.sysinfo.configure(
            '-t', '--time',
            help='Job execution time in ISO format.',
            required=False, type=datetime.fromisoformat,
            default=datetime.now())
        self.log.sysinfo.configure(
            '-a', '--auto',
            help='Indicates that job was launched automatically by scheduler.',
            required=False, action='store_true')
        self.log.sysinfo.process()

        self._time = self.log.sysinfo.args.time
        self.__auto = self.log.sysinfo.args.auto
        self._pid = self.log.sysinfo.stat.pid

        scheduler = self.config['SCHEDULER'].get('name').upper()
        user = self.log.sysinfo.stat['user'].upper()
        self._initiator = scheduler if self.__auto is True else user
        pass

    def run(self):
        """Basic method to start job script."""
        self.open()
        atexit.register(self.close)
        pass

    def open(self):
        """Open the job."""
        self.status = 'W'
        self._start_timestamp = datetime.now()

        self.log.header.add(
            pos='end', job=self._id,
            job_time=self._time.isoformat(sep=' ', timespec='seconds'),
            configs=', '.join(self.job_config.FILES),
            persons=', '.join(self._persons))
        self.log.head()

        history = self._database.history
        insert = history.insert().values(
            job=self._id, initiator=self._initiator,
            log=os.path.relpath(self.log.output.file.path), pid=self._pid,
            start_timestamp=self._start_timestamp, status=self.status)
        self._database.connection.execute(insert)

        select = sql.select([history.c.id]).where(sql.and_(
            history.c.job == self._id,
            history.c.start_timestamp == self._start_timestamp))
        self._history_id = self._database.connection.execute(select).scalar()

        self.log.info(f'Job <{self.name}> started at PID <{self._pid}>.')
        pass

    def close(self):
        """Close the job."""
        self._end_timestamp = datetime.now()
        self.status = 'D' if self.log.with_error is False else 'E'

        history = self._database.history
        update = history.update().\
            values(end_timestamp=self._end_timestamp, status=self.status).\
            where(history.c.id == self._history_id)
        self._database.connection.execute(update)
        self.spent = self._end_timestamp - self._start_timestamp
        self.log.info(f'Job finished.')
        self.log.info(f'Time spent: {self.spent.seconds} seconds.')
        pass

    def _select_details(self):
        schedule = self._database.schedule
        select = schedule.select().where(schedule.c.file == self._file)
        row = self._database.connection.execute(select).first()
        details = dict(row)
        return details

    @property
    def root(self):
        return self._root

    @property
    def id(self):
        return self._id

    @property
    def time(self):
        return self._time

    @property
    def auto(self):
        return self.__auto

    @property
    def initiator(self):
        return self._initiator

    @property
    def persons(self):
        return self._persons

    @property
    def history_id(self):
        return self._history_id

    @property
    def start_timestamp(self):
        return self._start_timestamp

    @property
    def end_timestamp(self):
        return self._end_timestamp
