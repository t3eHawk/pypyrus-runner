import os
import sys

def get_root():
    home = os.getenv('PYPYRUS_RUNNER_HOME')
    root = home or os.path.abspath(os.path.dirname(sys.argv[0]))
    os.chdir(root)
    return root

def join_persons(*args):
    persons = []
    for item in args:
        if isinstance(item, (list, tuple)) is True:
            persons.extend(item)
        elif isinstance(item, str) is True:
            persons.append(item)
    return persons
