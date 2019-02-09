import os
import sys
import shutil
import platform
import configparser

import pypyrus_tables as tables
import pypyrus_logbook as logbook

from datetime import datetime

from .job import Job
from .scheduler import Scheduler
from .parser import parse_schedule, parse_process

class Manager():
    """
    Main API with methods and CLI to communicate with, use or manage
    schedulers, jobs and other module components.
    """
    def __init__(self):
        # Move to executable directory.
        root = os.path.abspath(os.path.dirname(sys.argv[0]))
        os.chdir(root)
        self.root = root

        # Initialize log object that will log all messages to console by
        # default.
        self.log = logbook.Log('Manager', file=False, console=True)
        self.log.configure(format='{rectype}: {message}\n')

        # Initialize config object.
        config_path = os.path.abspath(f'{root}/config.ini')
        config_exists = os.path.exists(config_path)
        self.config = self.parse_config()
        if config_exists is False:
            self.log.info(f'File {os.path.abspath(config_path)} created.')

        try:
            # If argv more than one then command was entered.
            if len(sys.argv) > 1:
                # Get command that user entered. Maximum length is two words.
                func = '_'.join(sys.argv[1:3])
                call_func = getattr(self, func)
                # Get arguments that user entered. All that goes after second
                # word.
                args = sys.argv[3:]
                if len(args) == 1 and args[0] == 'help':
                    self.help(func)
                    return
                # Execute received command with arguments.
                call_func(*args)
            else:
                self.help()
        except BaseException:
            self.log.error()

        pass

    def parse_config(self, main='config.ini', save=True):
        """Parse the config object."""
        abspath = os.path.abspath(main)
        # Format the paths.
        config = configparser.ConfigParser(allow_no_value=True)
        # Give the default configuration.
        defaults = {
            'MANAGER': {
                'editor':
                    'notepad' if platform.system() == 'Windows' else 'nano'
            }
        }
        # Read the configuration in files.
        config.read(abspath)
        # Check and fill missing defaults.
        for section, options in defaults.items():
            if config.has_section(section) is False:
                config.add_section(section)
            for option, value in options.items():
                if config.has_option(section, option) is False:
                    config.set(section, option, value)
        if save is True:
            with open(abspath, 'w') as config_file:
                config.write(config_file)
        return config

    def help(self, topic='main'):
        """Show special application help note."""
        note = help_notes.get(topic)
        note = '\n'.join(note)
        print(note)
        pass

    def create_scheduler(self):
        """Create the scheduler with all necessary initial items."""
        self.log.subhead('create scheduler')

        root = self.root

        print('\nPlease follow the steps to create the scheduler.')

        # Get all inputs.
        scheduler_name = input('Enter the name or leave empty to use default:\n') or 'scheduler'
        scheduler_desc = input('Enter the description or leave empty to use default:\n') or 'Scheduler'

        self.log.bound()
        self.log.info(f'Creating scheduler {scheduler_name}...')

        # Define all scheduler items.
        scheduler_path = os.path.abspath(f'{root}/scheduler.py')
        config_path = os.path.abspath(f'{root}/config.ini')
        schedule_path = os.path.abspath(f'{root}/schedule.tsv')
        jobs_folder = os.path.abspath(f'{root}/jobs')

        # Create main scheduler file.
        if os.path.exists(scheduler_path) is False:
            with open(scheduler_path, "w+") as f:
                strings = '\n'.join([
                    'import pypyrus_runner as runner\n',
                    'scheduler = runner.Scheduler()\n',
                    'scheduler.start()\n',
                ])
                f.write(strings)
            self.log.info(f'File {scheduler_path} created.')
        else:
            self.log.warning(f'File {scheduler_path} already exists!')

        # Create configuration file.
        Scheduler.parse_config(config_path)
        self.log.info(f'File {config_path} updated.')

        # Create schedule.
        if os.path.exists(schedule_path) is False:
            with open(schedule_path, "w+") as f:
                strings = '\t'.join([
                    'ID', 'NAME', 'DESCRIPTION', 'ENVIRONMENT', 'FILE',
                    'MONTH_DAY', 'WEEK_DAY', 'HOUR', 'MINUTE', 'SECOND',
                    'PARAMETERS', 'STATUS\n'
                ])
                f.write(strings)
            self.log.info(f'File {schedule_path} created.')
        else:
            self.log.warning(f'File {schedule_path} already exists!')

        # Create folder for jobs.
        if os.path.exists(jobs_folder) is False:
            os.makedirs(jobs_folder)
            self.log.info(f'Folder {jobs_folder} created.')
        else:
            self.log.warning(f'Folder {jobs_folder} already exists!')

        pass

    def create_job(self):
        """Create the job with all necessary initial items."""
        self.log.subhead('create job')

        root = self.root

        # Check if some scheduler components are missing.
        not_found = tuple(filter(
            lambda item: not os.path.exists(item),
            (f'{root}/scheduler.py', f'{root}/config.ini',
            f'{root}/schedule.tsv')
        ))
        if len(not_found) > 0:
            self.log.warning('Some default scheduler components was not found!')
            self.log.warning('No %s' % ', '.join(not_found))
            self.log.bound()

        # Get the id for new job.
        current_jobs = tuple(map(
            lambda folder: int(folder),
            os.listdir('jobs/')))
        job_id = max(current_jobs) + 1 if len(current_jobs) > 0 else 0

        print('\nFollow the instructions to create the job.')
        print('Inputs with * are mandatory.')

        # Get all inputs.
        job_name = input('Enter the name or leave empty to use default:\n') or f'job_{job_id:03}'
        job_desc = input('Enter the short description:\n') or f'Job {job_id}'
        job_environment = input('Enter the environment or leave empty to use Python:\n') or 'python'
        job_month_day = input('Enter the month day (1-31):\n') or '*'
        job_week_day = input('Enter the week day (1-7):\n') or '*'
        job_hour = input('Enter the hour (0-23):\n') or '*'
        job_minute = input('Enter the minute (0-59):\n') or '*'
        job_second = input('Enter the second (0-59):\n') or '*'
        while True:
            job_status = input('Activate job (Y/N)? *:\n')
            if job_status in ('Y', 'N'):
                break

        self.log.bound()
        self.log.info('Creating job...')
        self.log.info(f'Job ID <{job_id}>')

        # Define all job items.
        job_folder = os.path.abspath(f'{root}/jobs/{job_id}')
        job_path = os.path.abspath(f'{job_folder}/job.py')
        config_path = os.path.abspath(f'{job_folder}/config.ini')
        script_path = os.path.abspath(f'{job_folder}/script.py')

        # Create folder with job.
        if os.path.exists(job_folder) is False:
            os.makedirs(job_folder)
            self.log.info(f'Folder {job_folder} created.')
        else:
            self.log.warning(f'Folder {job_folder} already exists!')
            self.log.critical('Existing job can not be replaced.' )

        # Create main job file.
        if os.path.exists(job_path) is False:
            strings = '\n'.join([
                'import pypyrus_runner as runner\n',
                'if __name__ == \'__main__\':',
                '    import script',
                'else:',
                '    job = runner.Job()',
                '    job.push()\n',
            ])
            with open(job_path, "w+") as f:
                f.write(strings)
            self.log.info(f'File {job_path} created.')
        else:
            self.log.warning(f'File {job_path} already exists!')

        # Create configuration file.
        if os.path.exists(config_path) is False:
            Job.parse_config(config_path)
            self.log.info(f'File {config_path} created.')
        else:
            self.log.warning(f'File {config_path} already exists!')

        # Create job script file.
        if os.path.exists(script_path) is False:
            strings = '\n'.join([
                'from job import job\n',
                '# Write the code to be executed by job down below.\n',
            ])
            with open(script_path, "w+") as f:
                f.write(strings)
            self.log.info(f'File {script_path} created.')
        else:
            self.log.warning(f'File {script_path} already exists!')

        # Add job to schedule.
        try:
            with open(f'{root}/schedule.tsv', 'a+') as f:
                strings = '\t'.join([
                    '{job_id}', '{job_name}', '{job_desc}',
                    '{job_environment}', '{job_path}',
                    '{job_month_day}', '{job_week_day}',
                    '{job_hour}', '{job_minute}', '{job_second}',
                    # Empty cell for parameters.
                    '',
                    '{job_status}\n'
                ]).format(**locals())
                f.write(strings)
        except BaseException:
            self.log.error(f'Job {job_name} was not added to schedule.')
            self.log.error()
        else:
            self.log.info(f'Job {job_name} successfully added to schedule!')

        pass

    def run_job(self, id, *args):
        """Execute the job by id and optionally by trigger."""
        self.log.subhead('run job')
        self.log.info(f'ID <{id}>')
        # Get scheduler config and schedule.
        config = Scheduler.parse_config(save=False)
        schedule_path = config['SCHEDULER'].get('schedule')
        job = parse_schedule(schedule_path).select(id=id)
        if job.COUNT_ROWS > 1:
            self.log.critical('Job ID is not unique!')
        else:
            # Log job characteristics.
            self.log.info(f'Name <{job.name[0]}>')
            self.log.info(f'Description <{job.description[0]}>')
            # Trigger is optional.
            if len(args) == 0:
                trigger = datetime.now().strftime('%Y-%m-%d/%H:%M:%S')
            elif len(args) == 1:
                trigger = f'{args[0]}'
            elif len(args) == 2:
                trigger = f'{args[0]}/{args[1]}'
            trigger_for_log = trigger.replace('/', ' ')
            self.log.info(f'Trigger <{trigger_for_log}>')
            sure = None
            while sure not in ('Y', 'n'):
                sure = input('\nAre you sure Y/n?\n')
                if sure == 'Y':
                    # Get all parameters for job process.
                    environment = job.environment[0]
                    file = job.file[0]
                    parameters = f'-t {trigger}'
                    executor = config['ENVIRONMENT'].get(environment)
                    # Launch job process.
                    self.log.info('Executing...')
                    parse_process(executor, file, parameters).wait()
                    self.log.info('Done!')
                else:
                    self.log.warning('Request canceled.')
        pass

    def run_jobs(self, path):
        """Execute the list of jobs from the file."""
        # Get the table with jobs ids and triggers.
        table = tables.Table(path=path, sep=' ', head=False)
        for row in table.ROWS:
            id = row[0]
            trigger = row[1]
            # Run all requested jobs.
            self.run_job(id, trigger)
        pass

    def list_jobs(self, *args):
        """List all jobs in the schedule."""
        # Get scheduler config and schedule.
        config = Scheduler.parse_config(save=False)
        schedule_path = config['SCHEDULER'].get('schedule')
        schedule = parse_schedule(schedule_path)
        # Return whole table if no additional arguments passed.
        if len(args) == 0:
            view = schedule
        # In other case return that requested.
        else:
            if args[0] in ('active', 'inactive'):
                if args[0] == 'active':
                    kwargs = {'status': 'Y'}
                elif args[0] == 'inactive':
                    kwargs = {'status': 'N'}
            else:
                # Warn that incorrect argument was used.
                self.log.warning(f'Unknown parameter - {args[0]}. See *list jobs help*.')
                return
            view = schedule.select(**kwargs)
        print(view)
        pass

    def delete_job(self, id):
        """Delete the job by id."""
        self.log.subhead('delete job')
        self.log.warning('THESE CHANGES CANNOT BE UNDONE!')
        # Get scheduler config and schedule.
        config = Scheduler.parse_config(save=False)
        schedule_path = config['SCHEDULER'].get('schedule')
        job = parse_schedule(schedule_path).select(id=id)
        if job.COUNT_ROWS > 1:
            self.log.critical('Job ID is not unique!')
        else:
            # Log job characteristics.
            self.log.info(f'Name <{job.name[0]}>')
            self.log.info(f'Description <{job.description[0]}>')

        sure = None
        while sure not in ('Y', 'n'):
            sure = input('\nAre you sure Y/n?\n')
            if sure == 'Y':
                # Folder with job.
                root = self.root
                folder = os.path.abspath(f'{root}/jobs/{id}')

                # Delete folder with job.
                try:
                    shutil.rmtree(folder)
                except:
                    self.log.critical()
                else:
                    self.log.info(f'Folder {folder} REMOVED.')

                # Delete record with job in schedule.
                try:
                    schedule = parse_schedule(schedule_path).filter(id=id)
                    schedule.write(schedule_path)
                except:
                    self.log.critical()
                else:
                    self.log.info(f'Record in {schedule_path} REMOVED.')

                self.log.info('Done!')

            elif sure == 'n':
                self.log.info('Request canceled.')
        pass

    def edit_job(self, id):
        """Open script.py of job in the selected editor."""
        # Get all parameters for edition process.
        editor = self.config['MANAGER'].get('editor')
        script_path = os.path.abspath(f'jobs/{id}/script.py')
        self.log.info(f'Editing {script_path}...')
        # Launch edition process and wait until it is completed.
        parse_process(editor, script_path).wait()
        self.log.info('Done!')
        pass

    def edit_config(self, *args):
        """Open config.ini in the selected editor."""
        # Get all parameters for edition process.
        editor = self.config['MANAGER'].get('editor')
        root = self.root
        if len(args) == 0:
            config_path = os.path.abspath(f'{root}/config.ini')
        elif len(args) == 2 and args[0] == 'job':
            config_path = os.path.abspath(f'{root}/jobs/{args[1]}/config.ini')
        if os.path.exists(config_path) is False:
            self.log.critical('No such configuration file!')
        else:
            self.log.info(f'Editing {config_path}...')
            # Launch edition process and wait until it is completed.
            parse_process(editor, config_path).wait()
            self.log.info('Done!')
        pass

    def edit_schedule(self):
        """Open schedule.tsv in the selected editor."""
        # Get all parameters for edition process.
        editor = self.config['MANAGER'].get('editor')
        # Get scheduler config.
        config = Scheduler.parse_config(save = False)
        schedule_path = config['SCHEDULER'].get('schedule')
        self.log.info(f'Editing {schedule_path}...')
        # Launch edition process and wait until it is completed.
        parse_process(editor, schedule_path).wait()
        self.log.info('Done!')
        pass

help_notes = {
'main': [
'',
'List of available commands:',
'',
'create scheduler    Generate a scheduler with all elements.',
'create job          Generate a job with all elements.',
'list jobs           Show all jobs registered in the schedule.',
'edit schedule       Open the schedule file in the editor.',
'',
'edit job            Open the job script in the editor.',
'run job             Execute the job by id with or without run time.',
'run jobs            Execute the jobs listed in the file.',
'delete job          Delete the job by id.',
'',
'edit config         Open one of the configuration files in the editor',
'',
'help                Show this message.',
'',
'For more details type [command] help.',
],
'create_scheduler': [
'',
'Generate a scheduler with all elements.',
],
'create_job': [
'',
'Generate a job with all elements.',
'',
'NAME - technical name. Use default or enter any desired.',
'DESCRIPTION - short description. Enter any desired or leave empty.',
'ENVIRONMENT - used environment for execution. Choose from the list of',
'pointed in the main config.',
'',
'MONTH_DAY - day of month in range 1-31.',
'WEEK_DAY - day of week in range 1-7.',
'HOUR - hour of day in range 0-23.',
'MINUTE - minute of hour in range 0-59.',
'SECOND - second of minute in range 0-59',
'',
'STATUS - Y for active, N for inactive. Jobs with N status are skipped by',
'scheduler and not executed.',
'',
'You can schedule jobs by manipulating with time fields next few ways:',
'1. Execute job at certain date and time.',
'   Time presented as integers.',
'   Job that must be executed every day at 23:59:59 must look like:',
'   --------------------',
'   |HOUR|MINUTE|SECOND|',
'   --------------------',
'   |23  |59    |59    |',
'',
'2. Execute job every time cycle.',
'   Time presented as integers starting with /.',
'   Job that must be executed every 5 minutes must look like:',
'   ---------------',
'   |MINUTE|SECOND|',
'   ---------------',
'   |/5    |0     |',
'',
'3. Execute job only during certain period.',
'   Time presented as integers going with commas or dash.',
'   Job that must be executed only at weekdays at 23:59:59 must look like:',
'   -----------------------------',
'   |WEEK_DAY|HOUR|MINUTE|SECOND|',
'   -----------------------------',
'   |1-5     |23  |59    |59    |',
'',
'   Job that must be executed only at Monday, Wednesday, Friday at 23:59:59',
'   must look like:',
'   -----------------------------',
'   |WEEK_DAY|HOUR|MINUTE|SECOND|',
'   -----------------------------',
'   |1,3,5   |23  |59    |59    |',
'',
'You can combine different types of record.',
],
'list_jobs': [
'',
'Show all jobs registered in the schedule.',
'Parameters:',
'active      Show all jobs with status - Y.',
'inactive    Show all jobs with status - N.',
],
'edit_schedule': [
'',
'Open the schedule file in the editor.'
],
'edit_job': [
'',
'Open the job script in the editor.',
'Parameters:',
'id  integer  Id of the job you want to edit.',
],
'run_job': [
'',
'Execute the job by id with or without run time.',
'Parameters:',
'id         integer                  Id of the job you want to run.',
'trigger    yyyy-mm-dd/hh24:mi:ss    Date with or without time in ISO format',
'           yyyy-mm-dd               for what you want to run the job.',
'',
],
'run_jobs': [
'',
'Execute the jobs listed in the file.',
'Parameters:',
'file    path to file where each row is an id and a trigger for certain job',
'        separated with a space.',
'',
],
'delete_job': [
'',
'Delete the job by id.',
'Parameters:',
'id    integer    Id of the job you want to delete.',
],
'edit_config': [
'',
'Open one of the configuration files in the editor.',
'Parameters:',
'No        open config.ini',
'job id    open job.ini for job with id',
],
}
