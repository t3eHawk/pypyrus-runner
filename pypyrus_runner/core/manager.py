import datetime as dt
import os
import platform
import pypyrus_logbook as logbook
import pypyrus_tables as tables
import signal
import sys

from .conf import make_config
from .db import Database
from .help import demo
from .operator import Operator
from .utils import get_root


class Manager():
    """Main user API with methods and CLI to communicate, use or manage
    schedulers, jobs and other Runner components.

    Attributes
    ----------
    root : str
        Root application folder in file system. If PYPYRUS_RUNNER_HOME
        environment variable is set then it is used otherwise location of
        Python script is used.
    config : pypyrus.runner.core.conf.Config
        Main application configurator.
    log : pypyrus.logbook.logger.Logger
        Main application logger used by manager to print some messages in
        console.
    """

    def __init__(self):
        # Define root directroy and move to it.
        self.root = get_root()
        self.config = make_config(debug=False)
        self.log = logbook.getlogger(debug=False, format='{rectype}: {message}\n')
        self.__operator = Operator()

        try:
            # If argv more than one then command was entered.
            if len(sys.argv) > 1:
                # Read command. Command length is two words as maximum.
                func = '_'.join(sys.argv[1:3])
                call_func = getattr(self, func)
                args = self.log.sysinfo.anons
                # All that goes after second word is the command parameters.
                if func == 'help' or 'help' in args:
                    self.help()
                    return
                # Execute received command with arguments.
                call_func()
            else:
                self.help()
        except:
            self.log.error()
        pass

    def help(self):
        """Show special application help note."""
        args = self.log.sysinfo.anons[:2]
        name = '_'.join(args) if len(args) > 0 else None
        if name == 'help' or name is None:
            funcs = ['create_scheduler', 'start_scheduler', 'stop_scheduler',
                     'restart_scheduler', 'create_job', 'edit_script',
                     'edit_job', 'enable_job', 'disable_job', 'delete_job',
                     'list_jobs', 'run_job', 'run_jobs', 'edit_config']
            docs = {}
            for func in funcs:
                doc = getattr(self, func).__doc__.splitlines()[0]
                docs[func] = doc
            text = demo.format(**docs)
        elif name in dir(self):
            func = getattr(self, name)
            text = func.__doc__
        print(text)
        pass

    def create_scheduler(self):
        """Create scheduler in current location.

        """
        self.log.subhead('create scheduler')
        self.log.write('\nPlease follow the steps to create the scheduler.\n')

        # Get all inputs.
        name = input('Enter the name or leave empty to use default:\n')
        desc = input('Enter the description or leave empty to use default:\n')

        self.log.bound()
        self.__operator.create_scheduler(name, desc)
        pass

    def start_scheduler(self):
        """Start scheduler.

        """
        system = platform.system()
        if system == 'Windows':
            exe = 'pythonw'
            params = None
        elif system == 'Linux':
            exe = 'python'
            params = '&'
        file = os.path.join(self.root, 'scheduler.py')
        process = self.__operator.make_process(exe, file, params=params)
        self.log.info(f'Scheduler started at PID <{process.pid}>.')
        pass

    def stop_scheduler(self):
        """Stop scheduler.

        """
        database = Database()
        select = database.status.select()
        result = database.connection.execute(select).first()
        if result is not None:
            try:
                    pid = result['pid']
                    os.kill(pid, signal.SIGINT)
            except OSError:
                self.log.warning(f'Scheduler at PID <{pid}> already closed.')
            else:
                update = database.status.update().\
                    values(end_date=dt.datetime.now()).\
                    where(database.status.c.pid == pid)
                database.connection.execute(update)
                self.log.info(f'Scheduler at PID <{pid}> stopped.')
        else:
            self.log.warning('Cannot find running scheduler')
        pass

    def restart_scheduler(self):
        """Restart scheduler.

        """
        self.stop_scheduler()
        self.start_scheduler()
        pass

    def report_scheduler(self):
        """Show current scheduler status.

        """
        database = Database()
        select = database.status.select()
        result = database.connection.execute(select).first()
        if result is not None:
            start_date = result['start_date']
            end_date = result['end_date']
            pid = result['pid']
            if end_date is None:
                self.log.info('Scheduler is working.')
                self.log.info(f'Started at {start_date:%Y-%m-%d %H:%M:%S} '\
                              f'with PID {pid}.')
            else:
                self.log.info('Scheduler is shutdown.')
                self.log.info(f'Closed at {end_date:%Y-%m-%d %H:%M:%S}')
        else:
            self.log.warning('Cannot find running scheduler')
        pass

    def create_job(self):
        """Create job in current scheduler.

        """
        self.log.subhead('create job')
        self.log.write('\nFollow the instructions to create the job.\n')

        # Get all inputs.
        name = input('Enter the name or leave empty to use default:\n')
        desc = input('Enter the short description:\n')
        env = input('Enter the environment or leave empty to use Python:\n')
        month_day = input('Enter the month day (1-31):\n')
        week_day = input('Enter the week day (1-7):\n')
        hour = input('Enter the hour (0-23):\n')
        minute = input('Enter the minute (0-59):\n')
        second = input('Enter the second (0-59):\n')
        while True:
            status = input('Are you sure (Y/n)? *:\n')
            if status in ('Y', 'n'):
                break

        if status == 'Y':
            self.log.bound()
            self.__operator.create_job(name, desc, env, month_day, week_day,
                                       hour, minute, second)
        else:
            self.log.warning('Operation was canceled.')
        pass

    def edit_job(self):
        """Configure job.

        """
        self.log.subhead('edit job')
        args = self.log.sysinfo.anons[2:]
        if len(args) < 2:
            self.log.warning('You need to point the job ID and the attribute '\
                             'to modify.')
        else:
            id = args[0]
            attribute = args[1]
            job = self.__operator.select_job(id=id)
            if attribute == 'name':
                name = job['name']
                self.log.info(f'Name <{name}>')
                name = input('Enter new name: ')
                self.__operator.edit_job(id, name=name)
            elif attribute == 'desc':
                desc = job['description']
                self.log.info(f'Description <{desc}>')
                desc = input('Enter new description: ')
                self.__operator.edit_job(id, desc=desc)
            elif attribute == 'env':
                env = job['environment']
                self.log.info(f'Description <{env}>')
                env = input('Enter new environment: ')
                self.__operator.edit_job(id, env=env)
            elif attribute == 'params':
                params = job['parameters']
                self.log.info(f'Parameters <{params}>')
                params = input('Enter new parameters: ')
                self.__operator.edit_job(id, params=params)
            elif attribute == 'schedule':
                month_day = job['month_day']
                self.log.info(f'Month day <{month_day}>')
                week_day = job['week_day']
                self.log.info(f'Week day <{week_day}>')
                hour = job['hour']
                self.log.info(f'Hour <{hour}>')
                minute = job['minute']
                self.log.info(f'Minute <{minute}>')
                second = job['second']
                self.log.info(f'Second <{second}>')

                month_day = input(f'Enter new month day: ')
                week_day = input(f'Enter new week day: ')
                hour = input('Enter new hour: ')
                minute = input('Enter new minute: ')
                second = input('Enter new second: ')

                self.__operator.edit_job(id, month_day=month_day,
                                       week_day=week_day, hour=hour,
                                       minute=minute, second=second)

            else:
                self.log.error(f'Unknown attribute - {attribute}')
            self.log.info(f'Job with id <{id}> was updated.')
        pass

    def edit_script(self):
        """Open job script in text editor.

        """
        # Get all parameters for edition process.
        editor = self.config.proxy['GENERAL'].get('editor')
        id = self.log.sysinfo.anons[2]
        path = os.path.abspath(f'{self.root}/jobs/{id}/script.py')
        self.log.info(f'Editing {path}...')
        # Launch edition process and wait until it is completed.
        self.__operator.make_process(editor, path).wait()
        self.log.info('Done!')
        pass

    def enable_job(self):
        """Activate job.

        """
        args = self.log.sysinfo.anons[2:]
        if len(args) >= 1:
            id = args[0]
            self.__operator.enable_job(id)
        else:
            log.error('You need to point the job ID!')
        pass

    def disable_job(self):
        """Deactivate job.

        """
        args = self.log.sysinfo.anons[2:]
        if len(args) >= 1:
            id = args[0]
            self.__operator.disable_job(id)
        else:
            log.error('You need to point the job ID!')
        pass

    def run_job(self, id=None, date=None):
        """Execute one job.

        Parameters:
          id         Job ID which you want to run (see schedule for that value).
          date       Job date in ISO format (YYYY-MM-DD/YYYY-MM-DDTHH24:MI:SS).

        Flags:
          -y, --yes  Do not ask to run the job
        """
        if hasattr(self.log.sysinfo.args, 'yes') is False:
            self.log.sysinfo.add('-y', '--yes',
                                 help='Do not ask to run the job.',
                                 required=False, action='store_true')
        yes = self.log.sysinfo.args.yes
        args = self.log.sysinfo.anons[2:]
        if len(args) == 0:
            self.log.error('You need to point the job ID!')
        else:
            self.log.subhead('run job')
            id = id or args[0]
            job = self.__operator.select_job(id=id)
            if job is None:
                self.log.warning(f'No job with ID <{id}> was found!')
            else:
                name = job['name']
                desc = job['description']
                self.log.info(f'ID <{id}>')
                self.log.info(f'Name <{name}>')
                self.log.info(f'Description <{desc}>')
                # Date is optional.
                if isinstance(date, str) is False:
                    if len(args) == 1:
                        date = dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                    elif len(args) == 2:
                        date = f'{args[1]}'
                    elif len(args) >= 3:
                        date = f'{args[1]}T{args[2]}'
                self.log.info(f'Time <{dt.datetime.fromisoformat(date)}>')
                if yes is False:
                    while True:
                        sure = input('Are you sure Y/n? ')
                        if sure in ('Y', 'n'):
                            yes = True if sure == 'Y' else False
                            break
                if yes is True:
                    self.__operator.run_job(job, date=date)
                else:
                    self.log.warning('Operation was canceled.')
        pass

    def run_jobs(self):
        """Execute many jobs.

        """
        args = self.log.sysinfo.anons[2:]
        path = args[0]
        table = tables.Table(path=path, sep=' ', head=False)
        for row in table.ROWS:
            id = row[0]
            date = row[1]
            if table.COUNT_COLS == 3:
                date = f'{date}T{row[2]}'
            self.run_job(id=id, date=date)
        pass

    def delete_job(self):
        """Delete all job data.

        """
        args = self.log.sysinfo.anons[2:]
        if len(args) == 0:
            self.log.error('You need to point the job ID!')
        else:
            self.log.subhead('delete job')
            id = args[0]
            job = self.__operator.select_job(id=id)
            if job is None:
                self.log.warning(f'No job with ID <{id}> was found!')
            else:
                self.log.warning('THESE CHANGES CANNOT BE UNDONE!')
                name = job['name']
                desc = job['description']
                self.log.info(f'ID <{id}>')
                self.log.info(f'Name <{name}>')
                self.log.info(f'Description <{desc}>')
                while True:
                    sure = input('Are you sure Y/n? ')
                    if sure in ('Y', 'n'):
                        break
                if sure == 'Y':
                    self.__operator.delete_job(id)
                elif sure == 'n':
                    self.log.warning('Operation was canceled.')
        pass

    def list_jobs(self):
        """Show all scheduled jobs as a table.

        """
        jobs = self.__operator.list_jobs()
        rows = []
        for i, job in enumerate(jobs):
            if i == 0:
                header = list([key.upper() for key in job.keys()])
                rows.append(header)
            data = list([str(cell) for cell in job.values()])
            rows.append(data)

        if len(rows) >= 1:
            table = tables.Table(rows=rows)
            self.log.write(table)
        pass

    def edit_config(self):
        """Open chosen configuration file in text editor.

        """
        # Get all parameters for edition process.
        editor = self.config.proxy['GENERAL'].get('editor')
        args = self.log.sysinfo.anons[2:]
        if len(args) == 0:
            path = os.path.abspath(f'{self.root}/config.ini')
        elif len(args) == 1:
            id = args[0]
            path = os.path.abspath(f'{self.root}/jobs/{id}/job.ini')
        self.log.info(f'Editing {path}...')
        # Launch edition process and wait until it is completed.
        self.__operator.make_process(editor, path).wait()
        self.log.info('Done!')
        pass
