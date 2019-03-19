import os
import re
import sys
import atexit

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
        root = os.path.abspath(f'{folder}/../../')
        os.chdir(folder)

        self.__file = file
        self.__folder = folder
        self.__root = root

        # Parse configuration objects.
        self.config = config = Config(self)
        self.job_config = job_config = JobConfig(self, custom=config)

        self.database = database = Database(self)
        self.details = details = database.select_job(file=file)
        self.id = details['id']
        self.name = name or details['name']
        self.desc = desc or details['description']

        # Emails for information and notifications.
        owner = config['MANAGER'].get('owner')
        persons = persons or job_config['JOB'].get('persons')
        self.persons = []
        if owner is not None: self.persons.extend(owner.split())
        if persons is not None: self.persons.extend(persons.split())
        self.log = log = logbook.Logger(
            self.name, desc=self.desc,
            console=job_config['LOG'].getboolean('console'),
            limit_by_day=job_config['LOG'].getboolean('limit_by_day'),
            limit_by_size=job_config['LOG'].getboolean('limit_by_size'),
            max_size=job_config['LOG'].getint('max_size'),
            err_formatting=job_config['ERROR'].getboolean('formatting'),
            alarming=job_config['ERROR'].getboolean('alarming'),
            email=config['EMAIL'].get('address'),
            ip=config['EMAIL'].get('ip'),
            port=config['EMAIL'].get('port'),
            user=config['EMAIL'].get('user'),
            password=config['EMAIL'].get('password'),
            tls=config['EMAIL'].getboolean('tls'),
            recipients=self.persons)

        log.sysinfo.configure(
            '-t', '--time',
            help='Job execution time in ISO format.',
            required=False, type=datetime.fromisoformat,
            default=datetime.now())
        log.sysinfo.configure(
            '-a', '--auto',
            help='Indicates that job was launched automatically by scheduler.',
            required=False, action='store_true')
        log.sysinfo.process()

        self.time = log.sysinfo.args.time
        self.auto = log.sysinfo.args.auto

        scheduler = config['SCHEDULER'].get('name').upper()
        user = log.sysinfo.stat['user'].upper()
        self.initiator = scheduler if self.auto is True else user
        pass

    def run(self):
        """Basic method to start job script."""
        self.open()
        atexit.register(self.close)
        pass

    def open(self):
        """Open the job."""
        self.START_TIMESTAMP = datetime.now()
        self.log.header.add(
            pos='end', job=self.id,
            job_time=self.time.isoformat(sep=' ', timespec='seconds'),
            configs=', '.join(self.job_config.FILES),
            persons=', '.join(self.persons))
        self.log.head()
        self.process_id = self.database.open_process(
            job=self.id, initiator=self.initiator,
            start_timestamp=self.START_TIMESTAMP)
        self.log.info('JOB STARTED.')
        pass

    def close(self):
        """Close the job."""
        self.END_TIMESTAMP = datetime.now()
        self.database.close_process(
            process_id=self.process_id, end_timestamp=self.END_TIMESTAMP,
            error=False)
        spent = self.END_TIMESTAMP - self.START_TIMESTAMP
        self.log.info('JOB FINISHED.')
        self.log.info(f'time SPENT: {spent.seconds} seconds.')
        pass

    @property
    def file(self):
        return self.__file

    @property
    def folder(self):
        return self.__folder

    @property
    def root(self):
        return self.__root
