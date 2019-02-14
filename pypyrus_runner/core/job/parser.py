import os
import re
import subprocess
import configparser

import pypyrus_tables as tables

from datetime import datetime

def parse_schedule(path):
    """Parse the schedule by path to the Table object."""
    schedule = tables.Table(path=path)
    # Store time when shedule was modififed.
    schedule.M_TIME = os.stat(path).st_mtime
    return schedule

def parse_process(executor, path, parameters=None):
    """Interface to open a process."""
    if executor is not None:
        if re.match(r'^.*(\\|/).*$', executor):
            executor = os.path.abspath(executor)

    if path is not None:
        path = os.path.abspath(path)

    command = [value for value in (executor, path) if value is not None]

    if parameters is not None:
        parameters = parameters.split()
        command.extend(parameters)

    return subprocess.Popen(command)
