import os
import sys
import platform
import configparser
import pypyrus_logbook as logbook

class Config():
    def __new__(self, visitor, custom=None, *args, **kwargs):
        v_class = visitor.__class__.__name__

        if hasattr(visitor, 'root') is True:
            root = visitor.root
        else:
            home = os.getenv('PYPYRUS_RUNNER_HOME')
            root = home or os.path.abspath(os.path.dirname(sys.argv[0]))

        if hasattr(visitor, 'log') is True:
            log = visitor.log
        else:
            log = logbook.Logger()

        path = os.path.abspath(f'{root}/config.ini')
        FILES = [path]
        if isinstance(custom, list) is True:
            FILES.extend(custom)
        elif isinstance(custom, str) is True:
            FILES.append(custom)

        config = configparser.ConfigParser(allow_no_value=True)
        save_file = False

        exists = os.path.exists(path)
        deployed = os.path.exists(os.path.abspath(f'{root}/scheduler.py'))
        if exists is False: save_file = True

        config.read(FILES)
        config.FILES = FILES

        # Describe all default settings.
        default = {}

        MANAGER = {
            'editor': 'notepad' if platform.system() == 'Windows' else 'vim',
            'owner': None}
        SCHEDULER = {
            'name': 'runner',
            'desc': 'Runner'}
        DATABASE = {
            'path': f'{root}/db.sqlite3'}
        LOG = {
            'console': 'False',
            'limit_by_day': 'True',
            'limit_by_size': 'True',
            'max_size': '10485760'}
        EMAIL = {
            'address': None,
            'host': None,
            'port': None,
            'user': None,
            'password': None,
            'tls': 'True'}
        ERROR = {
            'formatting': 'True',
            'alarming': 'True'}
        DEBUG = {
            'showtime': 'False',
            'showdelay': 'False'}
        ENVIRONMENT = {
            'python': os.path.basename(os.path.splitext(sys.executable)[0]),
            'cpp': 'cpp',
            'java': 'java'}

        default['MANAGER'] = MANAGER

        if v_class == 'Operator' and deployed is False:
            SCHEDULER['name'] = kwargs.get('name')
            SCHEDULER['desc'] = kwargs.get('desc')

        if v_class == 'Scheduler'\
        or (v_class == 'Operator' and deployed is False):
            default['SCHEDULER'] = SCHEDULER
            default['DATABASE'] = DATABASE
            default['LOG'] = LOG
            default['EMAIL'] = EMAIL
            default['ERROR'] = ERROR
            default['DEBUG'] = DEBUG
            default['ENVIRONMENT'] = ENVIRONMENT

        for section, options in default.items():
            if config.has_section(section) is False:
                config.add_section(section)
                save_file = True
            for option, value in options.items():
                if config.has_option(section, option) is False:
                    config.set(section, option, value)
                    save_file = True

        if save_file is True:
            with open(path, 'w') as fh:
                config.write(fh)
                if exists is True: log.info(f'File {path} updated.')
                else: log.info(f'File {path} created.')
        return config
