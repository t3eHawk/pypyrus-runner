import os
import sqlite3
import pypyrus_tables as tables
import pypyrus_logbook as logbook

from ..tools.config import Config

class Storage():
    def __init__(self, visitor):
        if hasattr(visitor, 'root') is True: root = visitor.root
        else: root = os.path.abspath(os.path.dirname(sys.argv[0]))
        self.root = root

        if hasattr(visitor, 'log') is True: log = visitor.log
        else: log = logbook.Log('config', file=False, console=True)
        self.log = log

        if hasattr(visitor, 'config') is True: config = visitor.config
        else: config = Config(self)
        self.config = config

        database = config['SCHEDULER'].get('database')
        schedule = config['SCHEDULER'].get('schedule')

        if database is not None:
            self.db = sqlite3.connect(database)
            self.db.row_factory = sqlite3.Row
            self.cursor = self.db.cursor()
            self.table = schedule
            self.path = database
            self.m_time = None
        else:
            self.db = None
            self.cursor = None
            self.table = None
            self.path = schedule
            self.m_time = os.stat(self.path).st_mtime

        pass

    def sked(self):
        db = self.db
        if db is not None:
            cursor = self.cursor
            table = self.table
            select = f'SELECT * FROM {table}'
            self.schedule = cursor.execute(select).fetchall()
        else:
            path = self.path
            table = tables.Table(path=path)
            schedule = []
            keys = table.DATA.keys()
            for i, ROW in enumerate(table.ROWS):
                if i > 0:
                    row = dict(zip(keys, ROW))
                    schedule.append(row)
            self.schedule = schedule
        pass

    def describe(self, **kwargs):
        id = kwargs.get('id')
        file = kwargs.get('file')
        db = self.db
        if db is not None:
            table = self.table
            cursor = self.cursor
            if id is not None:
                select = f"SELECT * FROM {table} WHERE id = {id}"
                job = cursor.execute(select).fetchone()
                return job
            if file is not None:
                select = f"SELECT * FROM {table} WHERE file = '{file}'"
                job = cursor.execute(select).fetchone()
                return job

    def open_process(self, **kwargs):
        db = self.db
        if db is not None:
            cursor = self.cursor
            job_id = kwargs.get('job_id')
            job_time = kwargs.get('job_time')
            initiator = kwargs.get('initiator')
            start_timestamp = kwargs.get('start_timestamp')
            status = 'W'
            insert = (
                f"INSERT INTO history (job_id, job_time, initiator, "\
                f"start_timestamp, status) VALUES ("\
                f"{job_id}, '{job_time}', '{initiator}', "\
                f"'{start_timestamp}', '{status}')")
            cursor.execute(insert)
            db.commit()

            select = (
                f"SELECT process_id FROM history WHERE job_id = {job_id} "\
                f"AND job_time = '{job_time}'"\
                f"AND initiator = '{initiator}'"\
                f"AND start_timestamp = '{start_timestamp}'"\
                f"AND status = '{status}'")
            process_id = cursor.execute(select).fetchone()[0]
            return process_id

    def close_process(self, error=False, **kwargs):
        db = self.db
        if db is not None:
            cursor = self.cursor
            process_id = kwargs.get('process_id')
            end_timestamp = kwargs.get('end_timestamp')
            status = 'E' if error is True else 'F'
            update = (
                f"UPDATE history SET end_timestamp = '{end_timestamp}', "\
                f"status = '{status}' WHERE process_id = {process_id}")
            cursor.execute(update)
            db.commit()
            pass

    def clean_audit(self):
        delete = f"DELETE FROM audit_schedule"
        self.cursor.execute(delete)
        self.db.commit()
        pass

    @property
    def modified(self):
        if self.db is not None:
            select = f"SELECT MAX(time) FROM audit_schedule"
            m_time = self.cursor.execute(select).fetchone()[0]
            if self.m_time != m_time:
                self.m_time = m_time
                return True
        else:
            m_time = os.stat(self.path).st_mtime
            if self.m_time != m_time:
                self.m_time = m_time
                return True
