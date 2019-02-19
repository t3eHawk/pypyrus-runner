import os
import sys
import platform
import configparser
import pypyrus_logbook as logbook

class Config():
    def __new__(self, visitor, custom=None, *args, **kwargs):
        v_class = visitor.__class__.__name__
        if v_class == 'Job':
            if hasattr(visitor, 'folder') is True: folder = visitor.folder
            else: folder = os.path.abspath(os.path.dirname(sys.argv[0]))

            if hasattr(visitor, 'log') is True: log = visitor.log
            else: log = logbook.Log('config', file=False, console=True)

            path = os.path.abspath(f'{folder}/job.ini')
            FILES = [path]
            if isinstance(custom, list) is True:
                FILES.extend(custom)
            elif isinstance(custom, str) is True:
                FILES.append(custom)

            config = configparser.ConfigParser(allow_no_value=True)
            save_file = False

            exists = os.path.exists(path)
            if exists is False: save_file = True

            config.read(FILES)
            config.FILES = FILES

            # Describe all default settings.
            default = {}

            JOB = {
                'persons': None}
            LOG = {
                'console': 'False',
                'limit_by_day': 'True',
                'limit_by_size': 'True',
                'max_size': '10485760'}
            ERROR = {
                'formatting': 'True',
                'alarming': 'True'}

            default['JOB'] = JOB
            default['LOG'] = LOG
            default['ERROR'] = ERROR

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
