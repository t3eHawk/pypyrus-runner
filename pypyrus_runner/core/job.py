import argparse
import atexit
import datetime as dt
import os
import re
import pypyrus_logbook as logbook
import sqlalchemy as sql
import sys

from .conf import read_config
from .db import Database
from .utils import join_persons


class Job():
    """This class represents a Runner job.
    Job is an automated process that must be executed by scheduler according
    to job trigger like timing.
    Job is a part of application. At database job presented as a single record
    with unique id in *schedule* table. At file system job presented as a
    single folder with few files inside including job.py, job.ini and script.py.
    Each of this file plays its own role in job process. File **job.py** for
    example declares `Job` object. File **job.ini** in its turn used as
    additional configuration file in addition to to main application
    configurator. If you wish to modify some parameter for that certain job
    but not for all application then **job.ini** is what you need. At finnally
    **script.py** is a file with code you want to be executed under this job.
    File **script.py** already have `Job` instance immported that can be used
    as well as all its attributes like `log`.

    Parameters
    ----------
    name: str, optional
        The argument is used to set `name` attribute.
    desc : str, optional
        The argument is used to set `desc` attribute.
    persons : str or list of str, optional
        The argument is used to set `persons` attribute.

    Attributes
    ----------
    config : pypyrus.runner.core.conf.Config
        Job configurator.
    id : int
        Unique job ID defined in schedule.
    name : str
        Job name - one of the fields in schedule. We usally use here technical
        job name e.g. *load_table*, *parse_site*.
    desc : str
        Job description - one of the fields in schedule. We usually use here
        public job name or short description like *Loader for table* or
        *Parser for site*.
    log : pypyrus.logbook.logger.Logger
        Job logger. Used by job to write to log some information. Also we
        usually use this logger in our job scripts to get advantage of one
        generic logger for all job process.
    date : datetime.datetime
        Job operation date. Can be defined with *-d*/*--date* flag in formats
        YYY-MM-DD or YYYY-MM-DDTHH24:MI:SS. We usually use that attribute in
        out scripts when dynamic date is requiered. It give opportunity to
        easily restart job for ceratin date.
    auto : bool
        That flag describes in which of two modes job is executuing: manual or
        automatic. In case of automatic execution it should be set to True.
        Why should? Because this attribute based on execution flag
        *-a*/*--auto* which is pretty easy to manipulate with. Scheduler is
        configured in that way that all job runs are making with that flag.
        So be sure do not use *auto* flag to prevent some problems with
        dependencies.
    persons : list of str
        The list of email adresses of persons who interested in job execution.
        Used as *recipients* argument in `logger.email` that mostly allow to
        recieve alarms but also can be usefull when you need to generate some
        report or notifications from job.
        Note that application owner always is a part of recipients.
    initiator : str
        The name of initiator. When job is running in automatic mode you will
        see scheduler name here. In manual mode it will be user name who run
        push the job.
        That is one of the parameters that is logging to history table.
    pid : int
        The OS PID that covers the job run.
        That is one of the parameters that is logging to history table.
    history_id : int
        Unique ID of job run defined in history table.
    start_date : datetime.datetime
        Factual date of job start.
        That is one of the parameters that is logging to history table.
    end_date :
        Factual date of job end.
        That is one of the parameters that is logging to history table.
    status :
        The attribute shows current job status that is changing during the
        job run. There can be only three values of status:

        +-------+--------------------------------------+
        | Value | Means  |      Description            |
        +-------+--------+-----------------------------+
        |W      |Working |Job is currently in progress |
        +-------+--------+-----------------------------+
        |D      |Done    |Job is successfully finished |
        +-------+--------+-----------------------------+
        |E      |Error   |Job finished with error      |
        +-------+--------+-----------------------------+

        That is one of the parameters that is logging to history table.
    """

    def __init__(self, name=None, desc=None, persons=None):
        self.__file = os.path.abspath(sys.argv[0])
        os.chdir(os.path.abspath(os.path.dirname(self.__file)))

        # Parse configuration objects.
        self.config = read_config(os.path.abspath('job.ini'))
        self.__database = Database()

        schedule = self.__database.schedule
        select = schedule.select().where(schedule.c.file == self.__file)
        details = self.__database.connection.execute(select).first()
        self.id = details.id
        self.name = name or details.name
        self.desc = desc or details.description

        # Emails for information and notifications.
        owner = self.config.read_one_from_general('owner')
        persons = persons or self.config.read_one_from_general('persons')
        recipients = self.config.read_one_from_logger('smtp.recipients')
        self._persons = join_persons(owner, persons, recipients)

        parser = argparse.ArgumentParser()
        parser.add_argument('-d', '--date', dest='date', required=False,
                            type=dt.datetime.fromisoformat,
                            default=dt.datetime.now(),
                            help='Job execution date in ISO format.')
        parser.add_argument('-a', '--auto', required=False, action='store_true',
                            help='Job is executing automatically')
        args = parser.parse_args()
        self._date = args.date
        self.__auto = args.auto

        params = self.config.read_all_from_logger()
        params['smtp']['recipients'] = self._persons
        self.log = logbook.getlogger(app=self.name, desc=self.desc, **params)

        scheduler = self.config.proxy['SCHEDULER'].get('name')
        username = self.log.sysinfo.desc['user']
        self._initiator = scheduler if self.__auto is True else username
        self._pid = self.log.sysinfo.desc.pid
        self._history_id = None
        self._start_date = None
        self._end_date = None
        self.status = None
        pass

    @property
    def date(self):
        """Getter for `date` attribute."""
        return self._date

    @property
    def auto(self):
        """Getter for `auto` attribute."""
        return self.__auto

    @property
    def persons(self):
        """Getter for `persons` attribute."""
        return self._persons

    @property
    def initiator(self):
        """Getter for `initiator` attribute."""
        return self._initiator

    @property
    def pid(self):
        """Getter for `pid` attribute."""
        return self._pid

    @property
    def history_id(self):
        """Getter for `history_id` attribute."""
        return self._history_id

    @property
    def start_date(self):
        """Getter for `start_date` attribute."""
        return self._start_date

    @property
    def end_date(self):
        """Getter for `end_date` attribute."""
        return self._end_date

    def run(self):
        """Basic method to start job script."""
        self.open()
        atexit.register(self.close)
        pass

    def open(self):
        """Announce job start:
        - Change status to W
        - Define start date.
        - Create history record.
        - Print header in textual logger.
        - Print starting message in textual logger.
        """
        self.status = 'W'
        self._start_date = dt.datetime.now()

        history = self.__database.history
        insert = history.insert().\
            values(job=self.id, initiator=self._initiator,
                   log=os.path.relpath(self.log.root.file.path), pid=self._pid,
                   start_date=self._start_date, status=self.status)
        result = self.__database.connection.execute(insert)
        self._history_id = result.inserted_primary_key[0]

        self.log.header.include(job=self.id, number=self._history_id,
                                date=f'{self._date:%Y-%m-%d %H:%M:%S}',
                                initiator=self._initiator,
                                persons=', '.join(self._persons))
        self.log.head()
        self.log.info(f'Job <{self.name}> started at PID <{self._pid}>.')
        pass

    def close(self):
        """Announce job finish.
        - Change status to D or E depending on how job was executed.
        - Define end date.
        - Update history record.
        - Estimate time spent.
        - Print ending message in textual logger.
        """
        self._end_date = dt.datetime.now()
        self.status = 'D' if self.log.with_error is False else 'E'

        history = self.__database.history
        update = history.update().\
            values(end_date=self._end_date, status=self.status).\
            where(history.c.id == self._history_id)
        self.__database.connection.execute(update)
        self.spent = self._end_date - self._start_date
        self.log.info(f'Job finished.')
        self.log.info(f'Time spent: {self.spent.seconds} seconds.')
        pass
