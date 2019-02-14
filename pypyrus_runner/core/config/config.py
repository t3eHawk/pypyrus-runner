import os
import platform
import configparser
import pypyrus_runner as runner

class Config():
    def __new__(self, party):
        root = party.root
        path = os.path.abspath(f'{root}/config.ini')
        save_file = False

        config = configparser.ConfigParser(allow_no_value=True)
        if os.path.exists(path) is True:
            config.read(path)
        else:
            save_file = True

        if isinstance(party, runner.Manager) is True:
            defaults = {
                'MANAGER': {
                    'editor':
                        'notepad' if platform.system() == 'Windows' else 'vim'
                }
            }
        elif isinstance(party, Scheduler) is True:
            defaults = {
                'SCHEDULER': {
                    'name': 'scheduler',
                    'desc': 'Scheduler',
                    'mode': 'db',
                    'schedule': os.path.abspath(f'{root}/db.sqlite3')
                },
                'INFO': {
                    'owner': None
                },
                'LOG': {
                    'console': 'False',
                    'limit_by_day': 'True',
                    'limit_by_size': 'True',
                    'max_size': '10485760'
                },
                'EMAIL': {
                    'address': None,
                    'ip': None,
                    'port': None,
                    'user': None,
                    'password': None,
                    'tls': 'True'
                },
                'ERROR': {
                    'formatting': 'True',
                    'alarming': 'True'
                },
                'DEBUG': {
                    'showtime': 'False',
                    'showdelay': 'False'
                },
                'ENVIRONMENT': {
                    'python':
                        os.path.basename(os.path.splitext(sys.executable)[0]),
                    'cpp': 'cpp',
                    'java': 'java'
                }
            }

        for section, options in defaults.items():
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
                party.log.info(f'File {path} created.')
        return config
