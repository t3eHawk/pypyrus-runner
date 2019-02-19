import os
import re
import shutil
import sqlite3
import subprocess
import pypyrus_logbook as logbook

from datetime import datetime

from ..tools.config import Config
from ..tools.storage import Storage

class Operator():
    def __init__(self, manager=None, log=None, root=None):
        self.manager = manager

        if manager is not None:
            log = manager.log
            root = manager.root

        log = log or logbook.Log('operator', file=False, console=True)
        root = root or os.path.abspath(os.path.dirname(sys.argv[0]))
        os.chdir(root)

        self.log = log
        self.root = root
        pass

    def create_scheduler(self, name, desc, db=True):
        root = self.root
        log = self.log
        app = os.path.abspath(f'{__file__}/../../../app/scheduler')

        name = name or 'runner'
        desc = desc or 'Runner'

        log.info(f'Creating scheduler <{name}>...')

        path = os.path.abspath(f'{root}/scheduler.py')
        database = os.path.abspath(f'{root}/db') if db is True else None
        schedule = 'schedule' if db is True else os.path.abspath(
            f'{root}/schedule')
        jobs = os.path.abspath(f'{root}/jobs')

        config = Config(
            self, name=name, desc=desc, database=database, schedule=schedule)
        folders = [jobs]
        for folder in folders:
            if os.path.exists(folder) is False:
                os.makedirs(folder)
                log.info(f'Folder {folder} created.')
            else:
                log.warning(f'Folder {folder} already exists!')
        files = [path, database if db is True else schedule]
        for file in files:
            filename = os.path.basename(file)
            if os.path.exists(file) is False:
                content = open(f'{app}/{filename}', 'br').read()
                with open(file, 'bw') as fp:
                    fp.write(content)
                    log.info(f'File {file} created.')
            else:
                log.warning(f'File {file} already exists!')
        pass

    def create_job(
        self, name, desc, env, month_day, week_day,
        hour, minute, second
    ):
        log = self.log
        app = os.path.abspath(f'{__file__}/../../../app/job')
        root = self.root
        config = Config(self)

        database = config['SCHEDULER'].get('database')
        schedule = config['SCHEDULER'].get('schedule')

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
        parameters = ''
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

        if database is not None:
            db = sqlite3.connect(database)
            cursor = db.cursor()
            insert = (
                f"INSERT INTO {schedule} (id, name, description, "\
                "environment, file, month_day, week_day, "\
                "hour, minute, second, parameters, status) VALUES ("\
                f"{id}, '{name}', '{desc}', '{env}', '{job}', "\
                f"'{month_day}', '{week_day}', "\
                f"'{hour}', '{minute}', '{second}', "\
                f"'{parameters}', '{status}')\n")
            try:
                cursor.execute(insert)
                db.commit()
            except:
                log.error(f'Job <{name}> was not added to schedule!')
                log.error()
            else:
                log.info(f'Job <{name}> successfully added to schedule!')
        else:
            try:
                with open(schedule, 'a') as fh:
                    fh.write(
                        f'{id}\t{name}\t{desc}\t{env}\t{job}\t'\
                        f'{month_day}\t{week_day}\t'\
                        f'{hour}\t{minute}\t{second}\t'\
                        f'{parameters}\t{status}\n')
            except:
                log.error(f'Job <{name}> was not added to schedule!')
                log.error()
            else:
                log.info(f'Job <{name}> successfully added to schedule!')
        pass

    def list_jobs(self):
        storage = Storage(self)
        storage.sked()
        return storage.schedule

    def edit_schedule(self):
        print('Not configured yet.')
        pass

    def edit_job(self):
        print('Not configured yet.')
        pass

    def enable_job(self, id):
        log = self.log
        storage = Storage(self)
        db = storage.db
        if db is not None:
            cursor = storage.cursor
            table = storage.table
            select = f'SELECT COUNT(*) FROM {table} WHERE id = {id}'
            count = cursor.execute(select).fetchone()[0]
            if count == 1:
                try:
                    update = (
                        f"UPDATE {table} SET status = 'Y' WHERE id = {id}")
                    cursor.execute(update)
                    db.commit()
                except:
                    log.critical()
                else:
                    log.info(f'Job with id <{id}> was enabled.')
            else:
                log.warning(f'No job with id <{id}> was found!')

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
            now = datetime.now()
            log.info(f'Started at {now:%Y-%m-%d %H:%M:%S}.')
            log.info('Executing...')
            # Job will run as separate process.
            self.make_process(exe, file, params).wait()
        except:
            log.error()
        finally:
            now = datetime.now()
            log.info(f'Finished at {now:%Y-%m-%d %H:%M:%S}.')
        pass

    def disable_job(self, id):
        log = self.log
        storage = Storage(self)
        db = storage.db
        if db is not None:
            cursor = storage.cursor
            table = storage.table
            select = f'SELECT COUNT(*) FROM {table} WHERE id = {id}'
            count = cursor.execute(select).fetchone()[0]
            if count == 1:
                try:
                    update = (
                        f"UPDATE {table} SET status = 'N' WHERE id = {id}")
                    cursor.execute(update)
                    db.commit()
                except:
                    log.critical()
                else:
                    log.info(f'Job with id <{id}> was disabled.')
            else:
                log.warning(f'No job with id <{id}> was found!')
        pass

    def delete_job(self, id):
        log = self.log
        root = self.root
        storage = Storage(self)
        db = storage.db
        if db is not None:
            cursor = storage.cursor
            table = storage.table
            select = f'SELECT COUNT(*) FROM {table} WHERE id = {id}'
            count = cursor.execute(select).fetchone()[0]
            if count == 1:
                try:
                    delete = f"DELETE FROM {table} WHERE id = {id}"
                    cursor.execute(delete)
                    db.commit()
                except:
                    log.critical()
                else:
                    log.info(f'Record in <{table}> was DELETED.')
            else:
                log.warning(f'No job with id <{id}> was found!')

        try:
            folder = os.path.abspath(f'{root}/jobs/{id}')
            shutil.rmtree(folder)
        except:
            log.critical()
        else:
            log.info(f'Folder {folder} was REMOVED.')

        log.info(f'Job with id <{id}> was successfully deleted.')
        pass

    def edit_config(self):
        print('Not configured yet.')
        pass

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
