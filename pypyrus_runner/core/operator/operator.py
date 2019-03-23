import os
import re
import sys
import signal
import shutil
import datetime
import subprocess
import pypyrus_logbook as logbook

from ..config import Config
from ..database import Database

class Operator():
    def __init__(self, manager=None, log=None, root=None):
        self._manager = manager

        if manager is not None:
            log = manager.log
            root = manager.root

        home = os.getenv('PYPYRUS_RUNNER_HOME')
        root = root or home or os.path.abspath(os.path.dirname(sys.argv[0]))
        os.chdir(root)
        self._root = root

        self.log = log or logbook.Logger()

        pass

    def create_scheduler(self, name, desc):
        root = self.root
        log = self.log
        app = os.path.abspath(f'{__file__}/../../../app')

        name = name or 'runner'
        desc = desc or 'Runner'

        log.info(f'Creating scheduler <{name}>...')

        scheduler = os.path.abspath(f'{root}/scheduler.py')
        jobs = os.path.abspath(f'{root}/jobs')

        config = Config(self, name=name, desc=desc)
        folders = [jobs]
        for folder in folders:
            if os.path.exists(folder) is False:
                os.makedirs(folder)
                log.info(f'Folder {folder} created.')
            else:
                log.warning(f'Folder {folder} already exists!')
        files = [scheduler]
        for file in files:
            filename = os.path.basename(file)
            if os.path.exists(file) is False:
                content = open(f'{app}/{filename}', 'br').read()
                with open(file, 'bw') as fp:
                    fp.write(content)
                    log.info(f'File {file} created.')
            else:
                log.warning(f'File {file} already exists!')

        db = Database(self)
        log.info(f'Schema deployed at {db.path}.')
        pass

    def start_scheduler(self):
        scheduler = os.path.abspath(f'{self._root}/scheduler.py')
        self.make_process('pythonw', scheduler)
        pass

    def stop_scheduler(self):
        database = Database(self)
        select = database.status.select()
        result = database.connection.execute(select).first()
        pid = result['pid']
        update = database.status.update().\
            values(end_timestamp=datetime.datetime.now()).\
            where(database.status.c.pid == pid)
        database.connection.execute(update)
        os.kill(pid, signal.SIGINT)
        pass

    def restart_scheduler(self):
        self.stop_scheduler()
        self.start_scheduler()
        pass

    def create_job(
        self, name, desc, env, month_day, week_day,
        hour, minute, second
    ):
        log = self.log
        app = os.path.abspath(f'{__file__}/../../../app/job')
        root = self.root
        config = Config(self)
        db = Database(self)

        jobs = tuple(map(lambda folder: int(folder), os.listdir('jobs/')))
        id = max(jobs) + 1 if len(jobs) > 0 else 0

        folder = os.path.abspath(f'{root}/jobs/{id}')
        job = os.path.abspath(f'{folder}/job.py')
        ini = os.path.abspath(f'{folder}/job.ini')
        script = os.path.abspath(f'{folder}/script.py')

        name = name or f'job_{id:03}'
        desc = desc or f'Job {id}'
        env = env or 'python'
        month_day = month_day or '*'
        week_day = week_day or '*'
        hour = hour or '*'
        minute = minute or '*'
        second = second or '*'
        params = ''
        status = 'N'

        log.info(f'Creating job with ID <{id}>...')

        folders = [folder]
        for folder in folders:
            if os.path.exists(folder) is False:
                os.makedirs(folder)
                log.info(f'Folder {folder} created.')
            else:
                log.warning(f'Folder {folder} already exists!')
        files = [job, ini, script]
        for file in files:
            filename = os.path.basename(file)
            if os.path.exists(file) is False:
                content = open(f'{app}/{filename}', 'br').read()
                with open(file, 'bw') as fp:
                    fp.write(content)
                    log.info(f'File {file} created.')
            else:
                log.warning(f'File {file} already exists!')

        insert = db.schedule.insert().values(
            id=id, name=name, description=desc, environment=env, file=job,
            month_day=month_day, week_day=week_day, hour=hour,
            minute=minute, second=second, parameters=params, status=status)

        try:
            db.connection.execute(insert)
        except:
            log.error(f'Job <{name}> was not added to schedule!')
            log.error()
        else:
            log.info(f'Job <{name}> successfully added to schedule!')
        pass

    def edit_job(
        self, id, name=None, desc=None, env=None, params=None, month_day=None,
        week_day=None, hour=None, minute=None, second=None
    ):
        db = Database(self)
        update = db.schedule.update().where(db.schedule.c.id == id)
        need = False
        if name:
            update = update.values(name=name)
            need = True
        if desc:
            update = update.values(description=desc)
            need = True
        if env:
            update = update.values(environment=env)
            need = True
        if params:
            update = update.values(parameters=params)
            need = True
        if month_day:
            update = update.values(month_day=month_day)
            need = True
        if week_day:
            update = update.values(week_day=week_day)
            need = True
        if hour:
            update = update.values(hour=hour)
            need = True
        if minute:
            update = update.values(minute=minute)
            need = True
        if second:
            update = update.values(second=second)
            need = True
        if need is True:
            db.connection.execute(update)
        pass

    def enable_job(self, id):
        log = self.log
        db = Database(self)
        schedule = db.schedule
        try:
            update = schedule.update().values(status='Y').where(schedule.c.id == id)
            db.connection.execute(update)
        except:
            log.critical()
        else:
            log.info(f'Job with id <{id}> was enabled.')
        pass

    def disable_job(self, id):
        log = self.log
        db = Database(self)
        schedule = db.schedule
        try:
            update = schedule.update().values(status='N').where(schedule.c.id == id)
            db.connection.execute(update)
        except:
            log.critical()
        else:
            log.info(f'Job with id <{id}> was disabled.')
        pass

    def run_job(self, job, time):
        log = self.log
        try:
            env = job['environment']
            file = job['file']
            params = job['parameters']
            params += f' -t {time}'
            config = Config(self)
            exe = config['ENVIRONMENT'].get(env)
            now = datetime.datetime.now()
            log.info(f'Started at {now:%Y-%m-%d %H:%M:%S}.')
            log.info('Executing...')
            # Job will run as separate process.
            self.make_process(exe, file, params).wait()
        except:
            log.error()
        finally:
            now = datetime.datetime.now()
            log.info(f'Finished at {now:%Y-%m-%d %H:%M:%S}.')
        pass

    def delete_job(self, id):
        log = self.log
        root = self.root
        db = Database(self)
        schedule = db.schedule

        try:
            delete = schedule.delete().where(schedule.c.id == id)
            db.connection.execute(delete)
        except:
            log.critical()
        else:
            log.info('Record in schedule was DELETED.')

        try:
            folder = os.path.abspath(f'{root}/jobs/{id}')
            shutil.rmtree(folder)
        except:
            log.critical()
        else:
            log.info(f'Folder {folder} was REMOVED.')

        log.info(f'Job with id <{id}> was successfully deleted.')
        pass

    def list_jobs(self):
        db = Database(self)
        select = db.schedule.select()
        result = db.connection.execute(select)
        jobs = list(map(lambda row: dict(row), result))
        return jobs

    def select_job(self, id):
        database = Database(self)
        schedule = database.schedule
        select = schedule.select().where(schedule.c.id == id)
        row = database.connection.execute(select).first()
        job = dict(row) if row is not None else None
        return job

    def make_process(self, exe, file, params=None):
        if exe is not None and re.match(r'^.*(\\|/).*$', exe) is not None:
            exe = os.path.abspath(exe)
        if file is not None:
            file = os.path.abspath(file)
        command = [exe, file]
        if params is not None:
            params = params.split()
            command.extend(params)
        return subprocess.Popen(command)

    @property
    def root(self):
        return self._root
