import os
import re
import sys
import time
import pypyrus_logbook as logbook

from .trigger import Trigger
from ..operator import Operator
from ..config import Config
from ..database import Database

class Scheduler():
    """Class describing the scheduler and its API."""
    def __init__(
        self, name=None, desc=None, config=None, db=None, schedule=None,
        showtime=None, showdelay=None
    ):
        # Move to root directory.
        self.root = root = os.path.abspath(os.path.dirname(sys.argv[0]))
        os.chdir(root)

        # Parse configuration.
        self.config = config = Config(self, custom=config)

        # Name and description.
        self.name = name or config['SCHEDULER'].get('name')
        self.desc = desc or config['SCHEDULER'].get('desc')

        self.showtime = showtime or config['DEBUG'].getboolean('showtime')
        self.showdelay = showdelay or config['DEBUG'].getboolean('showdelay')

        # Initialize log object using some parameters.
        self.log = logbook.Logger(
            self.name, desc=self.desc,
            console=config['LOG'].getboolean('console'),
            limit_by_day=config['LOG'].getboolean('limit_by_day'),
            limit_by_size=config['LOG'].getboolean('limit_by_size'),
            max_size=config['LOG'].getint('max_size'),
            err_formatting=config['ERROR'].getboolean('formatting'),
            alarming=config['ERROR'].getboolean('alarming'),
            debug=config['LOG'].getboolean('debug'))

        self.operator = Operator(self)
        self.database = Database(self)
        self.trigger = Trigger(self)
        pass

    def start(self):
        """Launch the scheduler."""
        self.log
        self.log.head()
        self.database.clean_audit()
        self.log.info(f'Scheduler <{self.name}> STARTED.')
        self.sked()
        self.sync_time()

        # Iterate scheduler process.
        while True:
            self.process()
        pass

    def sked(self):
        self.schedule = self.database.select_schedule()
        pass

    def debug(self):
        # Log current moment if it is needed.
        if self.showtime is True:
            ticktock = 'TICK' if int(self.__moment) % 2 == 0 else 'TOCK'
            self.log.debug(ticktock)
        # Log current delay if it is needed.
        if self.showdelay is True:
            self.log.debug(f'DELAY {self.__delay:0.5f}')
        pass

    def check(self):
        if self.database.modified is True:
            self.sked()
            self.log.info('SCHEDULE WAS UPDATED!')
        pass

    def scan(self):
        self.trigger.scan()
        pass

    def active(self):
        self.debug()
        # Check that schedule was not modified.
        self.check()
        # Find jobs that must be launched at current moment.
        self.scan()
        pass

    def passive(self):
        # Increment moment. Sleep till the next step.
        self.move_time()
        pass

    def process(self):
        """
        Basic scheduler process.
        All actions that must be done during one scheduler step.
        """
        # Active phase.
        self.active()
        # Passive phase.
        self.passive()
        pass

    def sync_time(self):
        """Set current scheduler moment."""
        self.__delay = 0
        self.__moment = time.time()
        self.log.info('TIME WAS SYNCHRONIZED')
        pass

    def move_time(self):
        delay = time.time() - self.__moment
        wait = 1.0 - delay
        try:
            time.sleep(wait)
        except ValueError:
            self.log.warning('TIME IS BROKEN!')
            self.sync_time()
        else:
            self.__moment += 1
        finally:
            self.__delay = delay
        pass

    @property
    def moment(self):
        """Current scheduler moment"""
        return self.__moment

    @property
    def delay(self):
        """Current scheduler delay"""
        return self.__delay
