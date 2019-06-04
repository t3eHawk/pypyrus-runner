import ast
import configparser
import os
import platform
import pypyrus_logbook as logbook
import sys


def make_config(*args, **kwargs):
    """Create Runner configurator as an object and as file and return it.

    Parameters
    ----------
    *args
        The varaible arguments is used for class constructor.
    **kwargs
        The keyword arguments is used for class constructor.

    Returns
    -------
    value : pypyrus_runner.conf.Config
        Runner main configurator.
    """
    return Config(*args, **kwargs)

def read_config(*args):
    """Create Runner configurator with read only (without creating file)
    option and return it.

    Parameters
    ----------
    *args
        The varaible arguments is used for class constructor.

    Returns
    -------
    value : pypyrus_runner.conf.Config
        Runner main configurator with `read_only`=`True`.
    """
    return Config(*args, read_only=True)

class Config():
    """This class represents main Runner Configurator that owns settings to
    configure all Runner elements like scheduler, manager and jobs.

    Main configuration file is a simple INI file located together with
    *manager.py* at *PYPYRUS_RUNNER_HOME*. If *PYPYRUS_RUNNER_HOME* is not
    set in environment varaibles then current location will be used instead.

    Parameters
    ----------
    *args
        The variable arguments is used as custom configurators paths.
    read_only : bool
        The argument is used to disable file creation. The default is False
        which means that after all parameters are parsed they will be saved
        to main file.
    debug : bool
        The argument is used to filter debug messages created during the
        configuration parsing. By default is False which means that no debug
        messages will be printed to logger.

    Attributes
    ----------
    log : pypyrus_logbook.logger.Logger
        Separated logger for configurator. We do not use here main application
        logger (that is used by config visitors like Manager, Scheduler or Job)
        because it configures with the use of Configurator.

    paths : list of str
        All used configuration files including main file that is a very first
        element in the list.
    proxy : configparser.ConfigParser
        The attribute reflects confgigurator data and methods. It is created
        with default parameters except `allow_no_value` that is set to True.
    """

    def __init__(self, *args, read_only=False, debug=False):
        self.log = logbook.getlogger(name='config', file=False, debug=debug)
        self.log.debug('Parsing config')

        root = os.getenv('PYPYRUS_RUNNER_HOME')
        root = root or os.path.abspath(os.path.dirname(sys.argv[0]))
        self.log.debug(f'Root at {root}')

        path = os.path.join(root, 'config.ini')
        self.paths = [path]
        self.paths.extend([path for path in args if path is not None])
        self.log.debug(f'Configuration files: {self.paths}')

        self.proxy = configparser.ConfigParser(allow_no_value=True)
        self.proxy.read(self.paths)
        self.log.debug('Custom configuration was read from files')
        if read_only is False:
            save_file = False
            exists = os.path.exists(path)
            if exists is False: save_file = True

            editor = 'notepad' if platform.system() == 'Windows' else 'vim'
            GENERAL = {'db': os.path.join(root, 'db.sqlite3'),
                       'editor': editor, 'owner': None}

            SCHEDULER = {'name': None, 'desc': None, 'showtime': 'False',
                         'showdelay': 'False'}

            LOGGER = {'console': 'False', 'file': 'True',
                      'file.directory': None, 'file.name': None,
                      'file.extension': None, 'email': 'False',
                      'smtp.address': None, 'smtp.host': None,
                      'smtp.port': None, 'smtp.tls': None, 'smtp.user': None,
                      'smtp.password': None, 'table': 'False',
                      'db.vendor': None, 'db.host': None, 'db.port': None,
                      'db.sid': None, 'db.user': None, 'db.password': None,
                      'db.schema': None, 'db.table': None,
                      'db.date_column': None, 'html': 'False', 'format': None,
                      'info': 'True', 'debug': 'False', 'warning': 'True',
                      'error': 'True', 'critical': 'True', 'alarming': 'True',
                      'control': 'True', 'maxsize': '10485760', 'maxdays': '1',
                      'maxlevel': '2', 'maxerrors': 'False'}

            python = os.path.basename(os.path.splitext(sys.executable)[0])
            ENVIRONMENTS = {'python': python, 'cpp': 'cpp', 'java': 'java'}
            default = {'GENERAL': GENERAL, 'SCHEDULER': SCHEDULER,
                       'LOGGER': LOGGER, 'ENVIRONMENTS': ENVIRONMENTS}

            for section, options in default.items():
                if self.proxy.has_section(section) is False:
                    self.log.debug(f'Section [{section}] is missing')
                    self.proxy.add_section(section)
                    save_file = True
                for option, value in options.items():
                    if self.proxy.has_option(section, option) is False:
                        self.log.debug(f'Option [{section}][{option}] '\
                                        'is missing')
                        self.proxy.set(section, option, value)
                        save_file = True

            if save_file is True:
                with open(path, 'w') as fh:
                    self.proxy.write(fh, space_around_delimiters=False)
                    if exists is True: self.log.info(f'File {path} updated.')
                    else: self.log.info(f'File {path} created.')
            self.log.debug('Default configuration was processed also')
        pass

    def __str__(self):
        keys = self.proxy.sections()
        return f'{keys}'

    __repr__ = __str__

    @property
    def general(self):
        """GENERAL section of Configurator that is include some basic
        parameters used by many Runner components."""
        return self.proxy['GENERAL']

    @property
    def scheduler(self):
        """SCHEDULER section of Configurator that is used to configure
        Scheduler."""
        return self.proxy['SCHEDULER']

    @property
    def logger(self):
        """LOGGER section of Configurator that is used to configure main
        application logger.
        """
        return self.proxy['LOGGER']

    @property
    def environments(self):
        """ENVIRONMENTS section of Configurator that is used to list all
        available environment used by jobs."""
        return self.proxy['ENVIRONMENTS']

    def read_all_from_logger(self):
        """Read all logger relevant parameters from COnfigurator.

        Returns
        -------
        parameters : dict
            Dictionary with arguments that may be used to configure Pypyrus
            Logger.
        """
        parameters = {}

        # Get all basic parameters.
        for key in ['console', 'file', 'email', 'html', 'table', 'format',
                    'info', 'debug', 'warning', 'error', 'critical', 'alarming',
                    'control', 'maxsize', 'maxdays', 'maxlevel', 'maxerrors']:
                        value = self.read_one_from_logger(key)
                        if value is not None:
                            parameters[key] = value

        # Get all file parameters.
        for key in ['file.directory', 'file.name', 'file.extension']:
            value = self.read_one_from_logger(key)
            if value is not None:
                key = key.replace('file.', '')
                parameters[key] = value

        # Get all SMTP parameters.
        parameters['smtp'] = {}
        for key in ['smtp.address', 'smtp.host', 'smtp.port', 'smtp.tls',
                    'smtp.user', 'smtp.password']:
                        value = self.read_one_from_logger(key)
                        if value is not None:
                            key = key.replace('smtp.', '')
                            parameters['smtp'][key] = value

        # Get all DB parameters.
        parameters['db'] = {}
        for key in ['db.vendor', 'db.host', 'db.port', 'db.sid', 'db.user',
                    'db.password', 'db.schema', 'db.table', 'db.date_column']:
                        value = self.read_one_from_logger(key)
                        if value is not None:
                            key = key.replace('db.', '')
                            parameters['db'][key] = value
        return parameters

    def read_one_from_general(self, name):
        """Ready only one requested parameter from GENERAL section.

        Parameters
        ----------
        name: str
            The argument is used for the name of parameter that must be read.

        Returns
        -------
        value : any
            The value of requested parameter. We use type validation and
            conversion here so the type of the returning value depends on
            itself.
        """
        raw_value = self.proxy['GENERAL'].get(name)
        value = self._validate_string_paramter(raw_value)
        return value

    def read_one_from_logger(self, name):
        """Ready only one requested parameter from LOGGER section.

        Parameters
        ----------
        name: str
            The argument is used for the name of parameter that must be read.

        Returns
        -------
        value : any
            The value of requested parameter. We use type validation and
            conversion here so the type of the returning value depends on
            itself.
        """
        raw_value = self.proxy['LOGGER'].get(name)
        value = self._validate_string_paramter(raw_value)
        return value

    def _validate_string_paramter(self, parameter):
        """Data type validator and convertor for string parameters.

        Parameters
        ----------
        parameter : any
            The argument is used as value that must be validated and probably
            converted.

        Returns
        -------
        value: any
            Initial value in most appropriate data type. If validation is
            failed then initial value as it was passed will be returned.
        """
        try:
            return ast.literal_eval(parameter)
        except:
            return parameter
