import os
import sys
import signal
import datetime
import platform
import pypyrus_tables as tables
import pypyrus_logbook as logbook

from .help import helper
from ..operator import Operator
from ..config import Config
from ..database import Database

class Manager():
    """
    Main API with methods and CLI to communicate with, use or manage
    schedulers, jobs and other module components.
    """
    def __init__(self):
        # Define root directroy and move to it.
        home = os.getenv('PYPYRUS_RUNNER_HOME')
        root = home or os.path.abspath(os.path.dirname(sys.argv[0]))
        deployed = os.path.exists(f'{root}/scheduler.py')
        os.chdir(root)

        self._root = root
        self._deployed = deployed

        self.log = logbook.Logger()
        self.log.configure(format='{rectype}: {message}\n')

        self.config = Config(self)
        self.operator = Operator(self)

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
        func = '_'.join(args) or 'main'
        note = helper.get(func)
        note = '\n'.join(note)
        print(note)
        pass

    def create_scheduler(self):
        """Create the scheduler with all necessary initial items."""
        log = self.log
        operator = self.operator

        log.subhead('create scheduler')

        log.write('\nPlease follow the steps to create the scheduler.\n')

        # Get all inputs.
        name = input('Enter the name or leave empty to use default:\n')
        desc = input('Enter the description or leave empty to use default:\n')

        log.bound()
        operator.create_scheduler(name, desc)
        pass

    def start_scheduler(self):
        system = platform.system()
        if system == 'Windows':
            exe = 'pythonw'
            params = None
        elif system == 'Linux':
            exe = 'python'
            params = '&'
        file = os.path.abspath(f'{self._root}/scheduler.py')
        process = self.operator.make_process(exe, file, params=params)
        self.log.info(f'Scheduler started at PID <{process.pid}>.')
        pass

    def stop_scheduler(self):
        try:
            database = Database(self)
            select = database.status.select()
            result = database.connection.execute(select).first()
            pid = result['pid']
            os.kill(pid, signal.SIGINT)
        except OSError:
            self.log.warning(f'Scheduler at PID <{pid}> already closed.')
        else:
            update = database.status.update().\
                values(end_timestamp=datetime.datetime.now()).\
                where(database.status.c.pid == pid)
            database.connection.execute(update)
            self.log.info(f'Scheduler at PID <{pid}> stopped.')
        pass

    def restart_scheduler(self):
        self.stop_scheduler()
        self.start_scheduler()
        pass

    def report_scheduler(self):
        database = Database(self)
        select = database.status.select()
        result = database.connection.execute(select).first()
        start_timestamp = result['start_timestamp']
        end_timestamp = result['end_timestamp']
        pid = result['pid']
        if end_timestamp is None:
            self.log.info('Scheduler is working.')
            self.log.info(
                f'Started at {start_timestamp:%Y-%m-%d %H:%M:%S} '\
                f'with PID {pid}.')
        else:
            self.log.info('Scheduler is shutdown.')
            self.log.info(f'Closed at {end_timestamp:%Y-%m-%d %H:%M:%S}')
        pass

    def create_job(self):
        """Create the job with all necessary initial items."""
        log = self.log
        operator = self.operator

        log.subhead('create job')

        log.write('\nFollow the instructions to create the job.\n')

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
            log.bound()
            operator.create_job(
                name, desc, env, month_day, week_day, hour, minute, second)
        else:
            log.warning('Operation was canceled.')
        pass

    def edit_job(self):
        self.log.subhead('edit job')
        args = self.log.sysinfo.anons[2:]
        if len(args) < 2:
            self.log.warning(
                'You need to point the job ID and the attribute to modify.')
        else:
            id = args[0]
            attribute = args[1]
            job = self.operator.select_job(id=id)
            if attribute == 'name':
                name = job['name']
                self.log.info(f'Name <{name}>')
                name = input('Enter new name: ')
                self.operator.edit_job(id, name=name)
            elif attribute == 'desc':
                desc = job['description']
                self.log.info(f'Description <{desc}>')
                desc = input('Enter new description: ')
                self.operator.edit_job(id, desc=desc)
            elif attribute == 'env':
                env = job['environment']
                self.log.info(f'Description <{env}>')
                env = input('Enter new environment: ')
                self.operator.edit_job(id, env=env)
            elif attribute == 'params':
                params = job['parameters']
                self.log.info(f'Parameters <{params}>')
                params = input('Enter new parameters: ')
                self.operator.edit_job(id, params=params)
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

                self.operator.edit_job(
                    id, month_day=month_day, week_day=week_day, hour=hour,
                    minute=minute, second=second)

            else:
                self.log.error(f'Unknown attribute - {attribute}')
            self.log.info(f'Job with id <{id}> was updated.')
        pass

    def edit_script(self):
        """Open script.py of job in the selected editor."""
        # Get all parameters for edition process.
        editor = self.config['MANAGER'].get('editor')
        id = self.log.sysinfo.anons[2]
        path = os.path.abspath(f'{self._root}/jobs/{id}/script.py')
        self.log.info(f'Editing {path}...')
        # Launch edition process and wait until it is completed.
        self.operator.make_process(editor, path).wait()
        self.log.info('Done!')
        pass

    def enable_job(self):
        log = self.log
        operator = self.operator
        args = log.sysinfo.anons[2:]
        if len(args) >= 1:
            id = args[0]
            operator.enable_job(id)
        else:
            log.error('You need to point the job ID!')
        pass

    def disable_job(self):
        log = self.log
        operator = self.operator
        args = log.sysinfo.anons[2:]
        if len(args) >= 1:
            id = args[0]
            operator.disable_job(id)
        else:
            log.error('You need to point the job ID!')
        pass

    def run_job(self, **kwargs):
        """Execute the job by id and optionally by trigger."""
        log = self.log
        log.sysinfo.configure(
            '-y', '--yes', help='Do not ask to run the job.',
            required=False, action='store_true')
        log.sysinfo.process()
        args = log.sysinfo.anons[2:]
        yes = log.sysinfo.args.yes
        if len(args) == 0:
            log.error('You need to point the job ID!')
        else:
            log.subhead('run job')
            id = kwargs.get('id', args[0])
            job = self.operator.select_job(id=id)
            if job is None:
                log.warning(f'No job with ID <{id}> was found!')
            else:
                name = job['name']
                desc = job['description']
                log.info(f'ID <{id}>')
                log.info(f'Name <{name}>')
                log.info(f'Description <{desc}>')
                # Time is optional.
                if len(args) == 1:
                    now = datetime.datetime.now().strftime('%Y-%m-%d/%H:%M:%S')
                    time = kwargs.get('time', now)
                elif len(args) == 2:
                    time = f'{args[1]}'
                elif len(args) >= 3:
                    time = f'{args[1]}/{args[2]}'
                time_for_log = time.replace('/', ' ')
                log.info(f'Time <{time_for_log}>')
                if yes is False:
                    while True:
                        sure = input('Are you sure Y/n? ')
                        if sure in ('Y', 'n'):
                            yes = True if sure == 'Y' else False
                            break
                if yes is True:
                    self.operator.run_job(job, time=time)
                else:
                    log.warning('Operation was canceled.')
        pass

    def run_jobs(self):
        """Execute the list of jobs from the file."""
        args = self.log.sysinfo.anons[2:]
        path = args[0]
        table = tables.Table(path=path, sep=' ', head=False)
        for row in table.ROWS:
            id = row[0]
            time = row[1]
            if table.COUNT_COLS == 3:
                time = f'{time}/{row[2]}'
            self.run_job(id=id, time=time)
        pass

    def delete_job(self):
        """Delete the job by id."""
        log = self.log
        args = log.sysinfo.anons[2:]
        if len(args) == 0:
            log.error('You need to point the job ID!')
        else:
            log.subhead('delete job')
            id = args[0]
            job = self.operator.select_job(id=id)
            if job is None:
                log.warning(f'No job with ID <{id}> was found!')
            else:
                log.warning('THESE CHANGES CANNOT BE UNDONE!')
                name = job['name']
                desc = job['description']
                log.info(f'ID <{id}>')
                log.info(f'Name <{name}>')
                log.info(f'Description <{desc}>')
                while True:
                    sure = input('Are you sure Y/n? ')
                    if sure in ('Y', 'n'):
                        break
                if sure == 'Y':
                    self.operator.delete_job(id)
                elif sure == 'n':
                    log.warning('Operation was canceled.')
        pass

    def list_jobs(self):
        """List all jobs in the schedule."""
        log = self.log
        operator = self.operator
        jobs = operator.list_jobs()
        rows = []
        for i, job in enumerate(jobs):
            if i == 0:
                header = list([key.upper() for key in job.keys()])
                rows.append(header)
            data = list([str(cell) for cell in job.values()])
            rows.append(data)

        if len(rows) >= 1:
            table = tables.Table(rows=rows)
            log.write(table)
        pass

    def edit_config(self):
        """Open config file in the selected editor."""
        # Get all parameters for edition process.
        editor = self.config['MANAGER'].get('editor')
        args = self.log.sysinfo.anons[2:]
        if len(args) == 0:
            path = os.path.abspath(f'{self._root}/config.ini')
        elif len(args) == 1:
            id = args[0]
            path = os.path.abspath(f'{self._root}/jobs/{id}/job.ini')
        self.log.info(f'Editing {path}...')
        # Launch edition process and wait until it is completed.
        self.operator.make_process(editor, path).wait()
        self.log.info('Done!')
        pass

    @property
    def root(self):
        return self._root

    @property
    def deployed(self):
        return self._deployed
