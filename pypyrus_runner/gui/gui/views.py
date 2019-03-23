import os
import pypyrus_runner as runner

from pyramid.view import view_config
from pyramid_sqlalchemy import Session

from .models import Schedule, History

home = os.getenv('PYPYRUS_RUNNER_HOME')
root = home or '../..'

session = Session
operator = runner.Operator(root=root)

@view_config(route_name='schedule', renderer='templates/schedule.pt')
def schedule(request):
    thead, tbody = Schedule.render()
    return {'thead': thead, 'tbody': tbody}

@view_config(route_name='history', renderer='templates/history.pt')
def history(request):
    thead, tbody = History.render()
    return {'thead': thead, 'tbody': tbody}

@view_config(route_name='jobs', renderer='templates/jobs.pt')
def jobs(request):
    buttons = []
    for shed in session.query(Schedule.id, Schedule.name).all():
        button = f"""<a href="/jobs/{shed.id}"><p>{shed.name}</p></a>"""
        buttons.append(button)
    buttons = '\n'.join(buttons)
    return {'buttons': buttons}

@view_config(route_name='logs', renderer='templates/logs.pt')
def logs(request):
    return {}

@view_config(route_name='settings', renderer='templates/settings.pt')
def settings(request):
    return {}

@view_config(route_name='test', renderer='templates/test.pt')
def test(request):
    return {}
