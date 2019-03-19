import os
import sqlalchemy as sql
import pypyrus_tables as tables
import pypyrus_logbook as logbook

from ..config import Config

class Database():
    def __init__(self, visitor):
        if hasattr(visitor, 'root') is True:
            self.root = visitor.root
        else:
            home = os.getenv('PYPYRUS_RUNNER_HOME')
            self.root = home or os.path.abspath(os.path.dirname(sys.argv[0]))

        if hasattr(visitor, 'log') is True:
            self.log = visitor.log
        else:
            self.log = logbook.Logger()

        if hasattr(visitor, 'config') is True:
            self.config = visitor.config
        else:
            self.config = Config(self)

        path = os.path.abspath(self.config['DATABASE'].get('path'))
        credentials = f'sqlite:///{path}'
        engine = sql.create_engine(credentials)
        metadata = sql.MetaData()
        connection = engine.connect()

        self._engine = engine
        self._metadata = metadata
        self._connection = connection

        self._schedule = self._make_schedule()
        self._history = self._make_history()
        self._audit = self._make_audit()

        self._path = path
        self._mtime = None
        pass

    def select_schedule(self):
        schedule = self._schedule
        connection = self._connection
        select = schedule.select()
        result = connection.execute(select)
        result = list(map(lambda row: dict(row), result))
        return result

    def select_job(self, id=None, file=None):
        schedule = self._schedule
        connection = self._connection
        select = schedule.select()
        if id is not None:
            select = select.where(schedule.c.id == id)
        elif file is not None:
            select = select.where(schedule.c.file == file)
        result = connection.execute(select).first()
        result = dict(result)
        return result

    def open_process(self, job, initiator, start_timestamp):
        history = self._history
        connection = self._connection

        status = 'W'
        insert = history.insert().values(
            job=job, initiator=initiator,
            start_timestamp=start_timestamp, status=status)
        connection.execute(insert)

        select = sql.select([history.c.process_id]).where(sql.and_(
            history.c.job == job, history.c.initiator == initiator,
            history.c.start_timestamp == start_timestamp,
            history.c.status == status))
        result = connection.execute(select).scalar()
        return result

    def close_process(self, process_id, end_timestamp, error):
        history = self._history
        connection = self._connection

        status = 'E' if error is True else 'F'
        update = history.update().\
            values(end_timestamp=end_timestamp, status=status).\
            where(history.c.process_id == process_id)

        connection.execute(update)
        pass

    def clean_audit(self):
        audit = self._audit
        connection = self._connection
        delete = audit.delete()
        connection.execute(delete)
        pass

    def _make_schedule(self):
        name = 'schedule'
        engine = self._engine
        metadata = self._metadata
        if engine.has_table(name) is True:
            table = sql.Table(
                name, metadata, autoload=True, autoload_with=engine)
            return table
        else:
            table = sql.Table(
                name, metadata,
                sql.Column('id', sql.Integer, primary_key=True),
                sql.Column('name', sql.String()),
                sql.Column('description', sql.String()),
                sql.Column('environment', sql.String()),
                sql.Column('file', sql.String()),
                sql.Column('month_day', sql.String(2)),
                sql.Column('week_day', sql.String(2)),
                sql.Column('hour', sql.String(2)),
                sql.Column('minute', sql.String(2)),
                sql.Column('second', sql.String(2)),
                sql.Column('parameters', sql.String()),
                sql.Column('status', sql.String(1)))
            table.create(engine)
            self.log.info(f'Table <{name}> created.')
            return table

    def _make_history(self):
        name = 'history'
        engine = self._engine
        metadata = self._metadata
        if engine.has_table(name) is True:
            table = sql.Table(
                name, metadata, autoload=True, autoload_with=engine)
            return table
        else:
            table = sql.Table(
                name, metadata,
                sql.Column('process_id', sql.Integer, primary_key=True),
                sql.Column('job', sql.Integer),
                sql.Column('initiator', sql.String()),
                sql.Column('start_timestamp', sql.DateTime),
                sql.Column('end_timestamp', sql.DateTime),
                sql.Column('status', sql.String(1)),
                sqlite_autoincrement=True)
            table.create(engine)
            self.log.info(f'Table <{name}> created.')
            return table

    def _make_audit(self):
        name = 'audit'
        engine = self._engine
        connection = self._connection
        metadata = self._metadata
        if engine.has_table(name) is True:
            table = sql.Table(
                name, metadata, autoload=True, autoload_with=engine)
            return table
        else:
            table = sql.Table(
                name, metadata,
                sql.Column('event_time', sql.DateTime),
                sql.Column('event_type', sql.String()))
            table.create(engine)
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
                connection.execute(stmt)
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
