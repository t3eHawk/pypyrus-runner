import os

import pypyrus_runner as runner

from pyramid.view import view_config

home = os.getenv('PYPYRUS_RUNNER_HOME')
root = home or '../..'

@view_config(route_name='schedule', renderer='templates/schedule.pt')
def schedule(request):
    operator = runner.Operator(root=root)
    jobs = operator.list_jobs()
    tbody = []
    for job in jobs:
        id = job['id']
        name = job['name']
        desc = job['description']
        env = job['environment']
        month_day = job['month_day']
        week_day = job['week_day']
        hour = job['hour']
        minute = job['minute']
        second = job['second']
        status = job['status']
        row = [
            f'<td>{id}</td>',
            f'<td>{name}</td>',
            f'<td>{desc}</td>',
            f'<td>{env}</td>',
            f'<td>{month_day}</td>',
            f'<td>{week_day}</td>',
            f'<td>{hour}</td>',
            f'<td>{minute}</td>',
            f'<td>{second}</td>',
            f'<td>{status}</td>']
        row = '\n'.join(row)
        row = f'<tr>{row}</tr>'
        tbody.append(row)
    tbody = '\n'.join(tbody)
    thead = """
        <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Description</th>
            <th>Environment</th>
            <th>Month Day</th>
            <th>Week Day</th>
            <th>Hour</th>
            <th>Minute</th>
            <th>Second</th>
            <th>Status</th>
        </tr>
    """

    return {'thead': thead, 'tbody': tbody}

@view_config(route_name='history', renderer='templates/history.pt')
def history(request):
    return {}

@view_config(route_name='jobs', renderer='templates/jobs.pt')
def jobs(request):
    buttons = []
    operator = runner.Operator(root=root)
    jobs = operator.list_jobs()
    for job in jobs:
        id = job['id']
        name = job['name']
        button = f"""<a href="/jobs/{id}">{name}</a>"""
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
