import os
import re
import sys
import time
import datetime
import configparser

import pypyrus_logbook as logbook

from .parser import parse_schedule, parse_process

class Scheduler():
    """Class describing the scheduler and its API."""
    def __init__(
        self, name=None, desc=None, config=None, schedule=None,
        showtime=None, showdelay=None, *args, **kwargs
    ):
        # Move to scheduler directory.
        root = os.path.abspath(os.path.dirname(sys.argv[0]))
        os.chdir(root)
        self.root = root

        # Parse configuration file.
        self.config_path = config
        self.config = self.parse_config(paths=self.config_path)

        # Name and description.
        self.name = name or self.config['SCHEDULER'].get('name')
        self.desc = desc or self.config['SCHEDULER'].get('desc')
        # Current scheduler moment.
        # Moment include active and passive phases.
        # In active phase a scheduler makes all necessary for scheduling
        # actions. In passive phase a scheduler sleep till the next moment.
        self.__moment = None

        # Path to schedule file.
        schedule_path = schedule or self.config['SCHEDULER'].get('schedule')
        # Parsed jobs from schedule file.
        self.schedule = parse_schedule(schedule_path)

        # Log or not each scheduler moment.
        self.showtime = showtime or self.config['LOG'].getboolean('showtime')
        self.showdelay = showdelay or self.config['LOG'].getboolean('showdelay')

        # Initialize log object using some parameters.
        self.log = logbook.Log(
            self.name, desc = self.desc,
            console = self.config['LOG'].getboolean('console'),
            limit_by_day = self.config['LOG'].getboolean('limit_by_day'),
            limit_by_size = self.config['LOG'].getboolean('limit_by_size'),
            max_size = self.config['LOG'].getint('max_size'))
        pass

    @property
    def moment():
        """Current scheduler moment"""
        return self.__moment

    @staticmethod
    def parse_config(main='config.ini', paths=None, save=True):
        """Parse the config object."""
        # Format the paths.
        if type(paths).__name__ in ('list', 'tuple', 'set'):
            paths = list(paths)
        else:
            paths = [paths] if paths is not None else []

        if main == 'config.ini':
            root = os.path.abspath(os.path.dirname(sys.argv[0]))
            main = f'{root}/{main}'
        abspaths = list(map(lambda arg: os.path.abspath(arg), [main, *paths]))
        config = configparser.ConfigParser(allow_no_value=True)
        # Give the default configuration.
        defaults = {
            'SCHEDULER': {
                'name': 'scheduler',
                'desc': 'Scheduler',
                'schedule': os.path.abspath('schedule.tsv')
            },
            'INFO': {
                'owner': None
            },
            'LOG': {
                'console': 'False',
                'limit_by_day': 'True',
                'limit_by_size': 'True',
                'max_size': '10485760',
                'showtime': 'False',
                'showdelay': 'False'
            },
            'EMAIL': {
                'address': None,
                'ip': None,
                'port': None,
                'user': None,
                'password': None,
                'tls': 'True'
            },
            'ENVIRONMENT': {
                'python': os.path.basename(os.path.splitext(sys.executable)[0]),
                'cpp': 'cpp',
                'java': 'java'
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
                    config.set(section, option, value)
        # Finally save configuration in main file.
        if save is True:
            with open(main, 'w') as main_file:
                config.write(main_file)
        return config

    def start(self):
        """Launch the scheduler."""
        self.log.head()
        self.log.info('%s STARTED.' % self.desc)
        # First scheduler moment.
        self._sync_time()

        # Iterate scheduler process.
        while True:
            self._process()
        pass

    def run_job(self, i):
        """Launch the job by index."""
        try:
            schedule = self.schedule
            id = schedule.id[i]
            file = schedule.file[i]
            parameters = schedule.parameters[i]
            environment = schedule.environment[i]
            parameters += ' -a'
            self.log.info(f'CREATING SUBPROCESS FOR JOB {id}')
            executor = self.config['ENVIRONMENT'].get(environment)
            # Job will run as separate process.
            parse_process(executor, file, parameters)
        except BaseException:
            self.log.error()
        else:
            self.log.ok()
        pass

    def _sync_time(self):
        """Set current scheduler moment."""
        self.log.info('SYNCHRONIZING THE TIME...')
        self.__moment = time.time()
        self.log.ok()
        pass

    def _check_schedule(self):
        """Check if schedule was modified. If yes then reparse it."""
        path = self.schedule.PATH
        m_time = os.stat(path).st_mtime
        if self.schedule.M_TIME != m_time:
            self.schedule = parse_schedule(path)
            self.log.info('Schedule UPDATED.')
        pass

    def _check_time(self, unit, base):
        """
        Analyze given time unit on conformity to timestamp.
        unit - time unit that must be checked.
        base - current time unit.
        """
        # Check if empty or *.
        if re.match(r'^(\*)$', unit) is not None:
            return True
        # Check if unit is lonely digit and equals to base.
        elif re.match(r'^\d+$', unit) is not None:
            unit = int(unit)
            return True if base == unit else False
        # Check if unit is a cycle and integer division with base is true.
        elif re.match(r'^/\d+$', unit) is not None:
            unit = int(re.search(r'\d+', unit).group())
            if unit == 0: return False
            return True if base % unit == 0 else False
        # Check if unit is a range and base is in this range.
        elif re.match(r'^\d+-\d+$', unit):
            unit = [int(i) for i in re.findall(r'\d+', unit)]
            return True if base in range(unit[0], unit[1] + 1) else False
        # Check if unit is a list and base is in this list.
        elif re.match(r'^\d+,\s*\d+.*$', unit):
            unit = [int(i) for i in re.findall(r'\d+', unit)]
            return True if base in unit else False
        # All other cases is not for the base.
        else:
            return False

    def _scan_schedule(self):
        """Get full job list from the schedule."""
        # Convert moment to time structure.
        timestamp = time.localtime(self.__moment)
        # Local copy of jobs.
        jobs = self.schedule
        for i, status in enumerate(jobs.status):
            # Must be active.
            if status == 'Y':
                # Month days in range 1-31
                if self._check_time(
                    jobs.month_day[i], timestamp.tm_mday) is True:
                    # Week days in range 1-7.
                    # By default has a range 1-6. Correct it by 1.
                    if self._check_time(
                        jobs.week_day[i], timestamp.tm_wday + 1) is True:
                        # Hours in range 0-23.
                        if self._check_time(
                            jobs.hour[i], timestamp.tm_hour) is True:
                            # Minutes in range 0-59.
                            if self._check_time(
                                jobs.minute[i], timestamp.tm_min) is True:
                                # Seconds in range 0-59.
                                if self._check_time(
                                    jobs.second[i], timestamp.tm_sec) is True:
                                    yield i

    def _move(self):
        """
        Increment the moment considering possible deviations from the real
        time.
        """
        delay = time.time() - self.__moment
        wait = 1.0 - delay
        try:
            time.sleep(wait)
        except ValueError:
            self.log.warning('TIME IS BROKEN!')
            self._sync_time()
        else:
            self.__moment += 1
        finally:
            if self.showdelay is True:
                self.log.info(f'DELAY: {delay:0.5f}')
        pass

    def _process(self):
        """
        Basic scheduler process.
        All actions that must be done during one scheduler step.
        """
        # Active phase.
        # Log current moment if it is needed.
        if self.showtime == True:
            self.log.info('')

        # Check that schedule was not modified.
        self._check_schedule()
        # Find jobs that must be launched at current moment.
        for i in self._scan_schedule():
            self.run_job(i)

        # Passive phase.
        # Increment moment. Sleep till the next step.
        self._move()
        pass
