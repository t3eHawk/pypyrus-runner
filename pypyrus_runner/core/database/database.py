import os
import sqlalchemy as sql
import pypyrus_tables as tables
import pypyrus_logbook as logbook

from ..config import Config

class Database():
    def __init__(self, visitor):
        if hasattr(visitor, 'root') is True:
            self._root = visitor.root
        else:
            home = os.getenv('PYPYRUS_RUNNER_HOME')
            self._root = home or os.path.abspath(os.path.dirname(sys.argv[0]))

        if hasattr(visitor, 'log') is True:
            self.log = visitor.log
        else:
            self.log = logbook.Logger()

        if hasattr(visitor, 'config') is True:
            self._config = visitor.config
        else:
            self._config = Config(self)

        path = os.path.abspath(self._config['DATABASE'].get('path'))
        credentials = f'sqlite:///{path}'
        engine = sql.create_engine(credentials)
        metadata = sql.MetaData()
        connection = engine.connect()

        self._engine = engine
        self._metadata = metadata
        self._connection = connection

        self._schedule = self._make_schedule()
        self._history = self._make_history()
        self._status = self._make_status()
        self._audit = self._make_audit()

        self._path = path
        self._mtime = None
        pass

    def _make_schedule(self):
        name = 'schedule'
        if self._engine.has_table(name) is True:
            table = sql.Table(
                name, self._metadata,
                autoload=True, autoload_with=self._engine)
            return table
        else:
            table = sql.Table(
                name, self._metadata,
                sql.Column('id', sql.Integer, primary_key=True),
                sql.Column('name', sql.String),
                sql.Column('description', sql.String),
                sql.Column('environment', sql.String),
                sql.Column('file', sql.String),
                sql.Column('month_day', sql.String(2)),
                sql.Column('week_day', sql.String(2)),
                sql.Column('hour', sql.String(2)),
                sql.Column('minute', sql.String(2)),
                sql.Column('second', sql.String(2)),
                sql.Column('parameters', sql.String),
                sql.Column('status', sql.String(1)))
            table.create(self._engine)
            self.log.info(f'Table <{name}> created.')
            return table

    def _make_history(self):
        name = 'history'
        if self._engine.has_table(name) is True:
            table = sql.Table(
                name, self._metadata,
                autoload=True, autoload_with=self._engine)
            return table
        else:
            table = sql.Table(
                name, self._metadata,
                sql.Column('id', sql.Integer, primary_key=True),
                sql.Column('job', sql.Integer),
                sql.Column('initiator', sql.String),
                sql.Column('log', sql.String),
                sql.Column('pid', sql.Integer),
                sql.Column('start_timestamp', sql.DateTime),
                sql.Column('end_timestamp', sql.DateTime),
                sql.Column('status', sql.String(1)),
                sqlite_autoincrement=True)
            table.create(self._engine)
            self.log.info(f'Table <{name}> created.')
            return table

    def _make_status(self):
        name = 'status'
        if self._engine.has_table(name) is True:
            table = sql.Table(
                name, self._metadata,
                autoload=True, autoload_with=self._engine)
            return table
        else:
            table = sql.Table(
                name, self._metadata,
                sql.Column('start_timestamp', sql.DateTime),
                sql.Column('end_timestamp', sql.DateTime),
                sql.Column('pid', sql.Integer))
            table.create(self._engine)
            self.log.info(f'Table <{name}> created.')
            return table

    def _make_audit(self):
        name = 'audit'
        if self._engine.has_table(name) is True:
            table = sql.Table(
                name, self._metadata,
                autoload=True, autoload_with=self._engine)
            return table
        else:
            table = sql.Table(
                name, self._metadata,
                sql.Column('event_time', sql.DateTime),
                sql.Column('event_type', sql.String))
            table.create(self._engine)
            triggers = []
            triggers.append([
                r"CREATE TRIGGER check_schedule_delete AFTER DELETE",
                r"ON schedule",
                r"BEGIN",
                r"INSERT INTO audit (event_time, event_type)",
                r"VALUES (datetime(), 'DELETE');",
                r"END"])
            triggers.append([
                r"CREATE TRIGGER check_schedule_insert AFTER INSERT",
                r"ON schedule",
                r"BEGIN",
                r"INSERT INTO audit (event_time, event_type)",
                r"VALUES (datetime(), 'INSERT');",
                r"END"])
            triggers.append([
                r"CREATE TRIGGER check_schedule_update AFTER UPDATE",
                r"ON schedule",
                r"BEGIN",
                r"INSERT INTO audit (event_time, event_type)",
                r"VALUES (datetime(), 'UPDATE');",
                r"END"])
            for trigger in triggers:
                stmt = '\n'.join(trigger)
                self._connection.execute(stmt)
            self.log.info(f'Table <{name}> created.')
            return table

    @property
    def path(self):
        return self._path

    @property
    def connection(self):
        return self._connection

    @property
    def schedule(self):
        return self._schedule

    @property
    def history(self):
        return self._history

    @property
    def status(self):
        return self._status

    @property
    def audit(self):
        return self._audit

    @property
    def modified(self):
        select = sql.select([sql.func.max(self._audit.c.event_time)])
        mtime = self.connection.execute(select).scalar()
        if mtime is None:
            return False
        elif self._mtime == mtime:
            return False
        else:
            self._mtime = mtime
            return True
