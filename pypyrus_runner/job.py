import os
import re
import sys
import atexit
import argparse
import configparser

import pypyrus_logbook as logbook

from datetime import date, datetime

from .scheduler import Scheduler
from .parser import parse_schedule

class Job():
    """Class describing job and its API"""
    def __init__(
        self, name=None, desc=None, config=None, persons=None, *args, **kwargs
    ):
        # Move to job directory.
        pwd = os.path.abspath(os.path.dirname(sys.argv[0]))
        os.chdir(pwd)
        root = os.path.abspath('../../')
        self.pwd = pwd
        self.root = root

        # Parse configuration objects.
        self.baseconfig = Scheduler.parse_config(
            main=f'{root}/config.ini', save=False)
        self.config = self.parse_config(paths=config, job=self)
        # Parse executor arguments.
        arguments = self._parse_arguments()

        schedule = self._get_schedule()
        self.id = schedule.id[0] if schedule is not None else None

        self.trigger = arguments.trigger
        self.auto = arguments.auto

        # Name of the application Launching by the job.
        name = name or self.config['JOB'].get('name')
        self.name = name if schedule is None else schedule.name[0]
        # Description of the application Launching by the job.
        desc = desc or self.config['JOB'].get('desc')
        self.desc = desc if schedule is None else schedule.description[0]
        # Emails for information and notifications.
        owner = self.baseconfig['INFO'].get('owner')
        persons = persons or self.config['JOB'].get('persons')
        self.persons = []
        if owner is not None:
            self.persons.extend(owner.split())
        if persons is not None:
            self.persons.extend(persons.split())

        # Initialize log object if requested.
        self.log = logbook.Log(
            self.name, desc=self.desc,
            console=self.config['LOG'].getboolean('console'),
            limit_by_day=self.config['LOG'].getboolean('limit_by_day'),
            limit_by_size=self.config['LOG'].getboolean('limit_by_size'),
            max_size=self.config['LOG'].getint('max_size'),
            email=self.baseconfig['EMAIL'].get('address'),
            ip=self.baseconfig['EMAIL'].get('ip'),
            port=self.baseconfig['EMAIL'].get('port'),
            user=self.baseconfig['EMAIL'].get('user'),
            password=self.baseconfig['EMAIL'].get('password'),
            tls=self.baseconfig['EMAIL'].getboolean('tls'),
            recipients=self.persons)
        pass

    @staticmethod
    def parse_config(main='config.ini', paths=None, save=True, job=None):
        """Parse the config object."""
        # Format the paths.
        if type(paths).__name__ in ('list', 'tuple', 'set'):
            paths = list(paths)
        else:
            paths = [paths] if paths is not None else []

        if main == 'config.ini':
            pwd = job.pwd
            main = f'{pwd}/{main}'
        abspaths = list(map(lambda arg: os.path.abspath(arg), [main, *paths]))
        config = configparser.ConfigParser(allow_no_value=True)
        # Give the default configuration.
        defaults = {
            'JOB': {
                'persons': None
            },
            'LOG': {
                'console': 'False',
                'limit_by_day': 'False',
                'limit_by_size': 'True',
                'max_size': '10485760'
            }
        }
        # Read the configuration in files.
        config.read(abspaths)
        # Check and fill missing defaults.
        for section, options in defaults.items():
            if config.has_section(section) is False:
                config.add_section(section)
            for option, value in options.items():
                if config.has_option(section, option) is False:
                    if value is not None:
                        config.set(section, option, value)
                    else:
                        config.set(section, option)
        config.PATHS = abspaths
        # Finally save configuration in main file.
        if save is True:
            with open(main, 'w') as main_file:
                config.write(main_file)
        return config

    def push(self):
        """Basic method to start job script."""
        self.start_time = datetime.now()
        self.open()
        atexit.register(self.close)
        pass

    def open(self):
        """Open the job."""
        kwargs = {
            'id': self.id,
            'trigger': self.trigger.isoformat(sep=' ', timespec='seconds'),
            'configs': ', '.join(self.config.PATHS),
            'persons': ', '.join(self.persons)
        }
        self.log.header.add(pos='end', **kwargs)
        self.log.head()
        self.log.info('JOB STARTED.')
        pass

    def close(self):
        """Close the job."""
        spent = datetime.now() - self.start_time
        self.log.info('JOB FINISHED.')
        self.log.info('TIME SPENT: %s seconds.' % spent.seconds)
        pass

    def _parse_arguments(self):
        """Initialize the trigger."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-t', '--trigger',
            help='Pass to job certain run time in format YYYYMMDD/YYYY-MM-DD/YYYYMMDDHH24MISS',
            required=False, type=datetime.fromisoformat,
            default=datetime.now())
        parser.add_argument(
            '-a', '--auto',
            help='Indicates that job was launched automatically by scheduler.',
            required=False, action='store_true')
        arguments = parser.parse_args()
        return arguments

    def _get_schedule(self):
        """Extract record for current job from schedule."""
        schedule_path = self.baseconfig['SCHEDULER'].get('schedule')
        if schedule_path is not None:
            filepath = os.path.abspath(os.path.basename(sys.argv[0]))
            schedule = parse_schedule(schedule_path).select(file=filepath)
            if schedule.COUNT_ROWS == 1:
                return schedule
        return None
