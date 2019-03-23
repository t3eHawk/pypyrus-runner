from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from pyramid_sqlalchemy import BaseObject, Session

session = Session

class Schedule(BaseObject):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    environment = Column(String)
    month_day = Column(String(2))
    week_day = Column(String(2))
    hour = Column(String(2))
    minute = Column(String(2))
    second = Column(String(2))
    status = Column(String(1))

    def render():
        tbody = []
        thead = [
            '<th class="schedule-table-id">ID</th>',
            '<th class="schedule-table-name">Name</th>',
            '<th class="schedule-table-desc">Description</th>',
            '<th class="schedule-table-env">Environment</th>',
            '<th class="schedule-table-mday">Month Day</th>',
            '<th class="schedule-table-wday">Week Day</th>',
            '<th class="schedule-table-hour">Hour</th>',
            '<th class="schedule-table-min">Minute</th>',
            '<th class="schedule-table-sec">Second</th>',
            '<th class="schedule-table-status">Status</th>']
        thead = ''.join(thead)
        thead = f'<tr>{thead}</tr>'
        for row in session.query(Schedule).all():
            trows = [
                f'<td class="schedule-table-id">{row.id}</td>',
                f'<td class="schedule-table-name">{row.name}</td>',
                f'<td class="schedule-table-desc">{row.description}</td>',
                f'<td class="schedule-table-env">{row.environment}</td>',
                f'<td class="schedule-table-mday">{row.month_day}</td>',
                f'<td class="schedule-table-wday">{row.week_day}</td>',
                f'<td class="schedule-table-hour">{row.hour}</td>',
                f'<td class="schedule-table-min">{row.minute}</td>',
                f'<td class="schedule-table-sec">{row.second}</td>',
                f'<td class="schedule-table-status">{row.status}</td>']
            trows = ''.join(trows)
            trows = f'<tr>{trows}</tr>'
            tbody.append(trows)
        tbody = '\n'.join(tbody)
        return (thead, tbody)

class History(BaseObject):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True)
    job = Column(Integer, ForeignKey('schedule.id'))
    initiator = Column(String)
    log = Column(String)
    pid = Column(Integer)
    start_timestamp = Column(DateTime)
    end_timestamp = Column(DateTime)
    status = Column(String(1))

    def render():
        tbody = []
        thead = [
            '<th class="history-table-id">id</th>',
            '<th class="history-table-job">job</th>',
            '<th class="history-table-initiator">initiator</th>',
            '<th class="history-table-pid">pid</th>',
            '<th class="history-table-start">start timestamp</th>',
            '<th class="history-table-end">end timestamp</th>',
            '<th class="history-table-status">status</th>']
        thead = ''.join(thead)
        thead = f'<tr>{thead}</tr>'
        query = session.query(History, Schedule).join(Schedule)
        for hist, sched in query.all():
            trows = [
                f'<td class="history-table-id">{hist.id}</td>',
                f'<td class="history-table-job">{sched.name}</td>',
                f'<td class="history-table-initiator">{hist.initiator}</td>',
                f'<td class="history-table-pid">{hist.pid}</td>',
                '<td class="history-table-start">'\
                    f'{hist.start_timestamp: %Y-%m-%d %H:%M:%S}</td>',
                '<td class="history-table-end">'\
                    f'{hist.end_timestamp: %Y-%m-%d %H:%M:%S}</td>',
                f'<td class="history-table-status">{hist.status}</td>']
            trows = ''.join(trows)
            trows = f'<tr>{trows}</tr>'
            tbody.append(trows)
        tbody = '\n'.join(tbody)
        return (thead, tbody)
