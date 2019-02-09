# runner
The aim of this project is to create simple and effective instrument for automatic job scheduling and management in Python.

Main *runner* features:
* Minimal and user friendly command line interface.
* Cross platform - application can be used in any OS with Python 3.
* Opportunity to handle all jobs in one place instead of using many (Oracle Enterprise Scheduler, Linux Crontab and etc.).
* Generate built-in scheduler.
* Generate built-in job.
* Edit generated built-in jobs.
* Delete generated built-in jobs.
* Configuration with ini files.
* Automatic job scheduling and execution at certain time, during certain period or each time cycle.
* Manual job execution for now or for certain date and time.
* Scheduling with simple tsv file.
* Run jobs using virtual Python environment.
* Run jobs implemented in non Python technologies like C++, Java, Bash, Perl, etc.
* Built-in logging.
* Built-in notifications and alarms.

Main *runner* targets:
* Add some CLI commands.
* Attach database to *runner* as option for schedule and new data streams storage.
* Add simple web GUI.
* Improve notifications' mechanism and how they looks.
* Optimizations.

## Getting Started
### Requirements
Operation systems: Windows, Linux, Mac OS.

Python version: 3.7.1.

Python modules dependencies (use latest releases): [logbook](https://github.com/t3eHawk/logbook), [tables](https://github.com/t3eHawk/tables), [notifier](https://github.com/t3eHawk/notifier)

### Installation
To install just download the latest *[runner](https://github.com/t3eHawk/runner/releases)* release and copy /src/runner folder to your/python/folder/Lib/site-packages/.

## How to Use
To start working with *runner* you need just one simple file containing *runner.Manager* instance.

Let's go to the root of your disk *C:\* (or any other location, it does not matter) and create the folder *runner*.
Move to that folder and create new file named *manager.py* with next few string of code.
```
> C:\runner\manager.py

import runner

manager = runner.Manager()
```
Now *manager.py* is your main *runner* interface and the way to deploy the application in *C:\runner* folder.

Execute the *manager.py*. You will receive the main help note that can also be called with the *manager.py help*.

When you execute *manager.py* first time it generates main configuration file *config.ini* in the same folder.
```
$ python manager.py
INFO: File C:\runner\config.ini created.

List of available commands:

create scheduler    Generate a scheduler with all elements.
create job          Generate a job with all elements.
list jobs           Show all jobs registered in the schedule.
edit schedule       Open the schedule file in the editor.

edit job            Open the job script in the editor.
run job             Execute the job by id with or without run time.
run jobs            Execute the jobs listed in the file.
delete job          Delete the job by id.

edit config         Open one of the configuration files in the editor.

help                Show this message.

For more details type [command] help.                              
```
You could get more specific help for each command:
```
$ python manager.py run job help

Execute the job by id with or without run time.
Parameters:
id         integer                  Id of the job you want to run.
trigger    yyyy-mm-dd/hh24:mi:ss    Date with or without time in ISO format
           yyyy-mm-dd               for what you want to run the job.
```
We recommend to repeat that action for each command for more understanding.

### Create Scheduler
Type command *create scheduler* to generate the scheduler.
You will be asked about necessary attributes and then scheduler will be generated in the folder.
```
$ python manager.py create scheduler

Please follow the steps to create the scheduler.
Enter the name or leave empty to use default:

Enter the description or leave empty to use default:

********************************************************************************
INFO: Creating scheduler scheduler...
INFO: File C:\runner\scheduler.py created.
INFO: File C:\runner\config.ini updated.
INFO: File C:\runner\schedule.tsv created.
INFO: Folder C:\runner\jobs created.
```
About files:

*C:\runner\scheudler.py* - scheduler instance and starter.

*C:\runner\config.ini* - main configuration file.

*C:\runner\schedule.tsv* - job schedule.

*C:\runner\jobs* - folder for future jobs.

### Start Scheduler
To run the scheduler just execute file *scheduler.py*.
```
$ python scheduler.py
```
Now the scheduler is working.
Logs can be found in the folder *C:\runner\logs*.

To stop the scheduler process just type the CTRL + C.

### Create Job
Scheduler is ready and jobs can be created.

Type command *create job* to generate the job.
You will be asked about necessary attributes and then job will be generated.
```
$ python manager.py create job

Follow the instructions to create the job.
Inputs with * are mandatory.
Enter the name or leave empty to use default:
test
Enter the short description:
Test Job
Enter the environment or leave empty to use Python:

Enter the month day (1-31):

Enter the week day (1-7):

Enter the hour (0-23):
8
Enter the minute (0-59):
0
Enter the second (0-59):
0
Activate job (Y/N)? *:
N
********************************************************************************
INFO: Creating job...
INFO: Job ID: 0
INFO: Folder C:\runner\jobs\0 created.
INFO: File C:\runner\jobs\0\job.py created.
INFO: File C:\runner\jobs\0\config.ini created.
INFO: File C:\runner\jobs\0\script.py created.
INFO: Job test successfully added to schedule!
```
About files:

*C:\runner\jobs\0* - this is a job folder which corresponds to job id.

*C:\runner\jobs\0\job.py* - job instance and starter.

*C:\runner\jobs\0\config.ini* - job configuration file.

*C:\runner\jobs\0\script.py* - script that must be executed by job.

In *schedule.tsv* new record for created job will be provided.

Note that we used status *N*.
Jobs with such status will be not executed until status changed to Y.
It is done to prevent accidental job run before it is not finalized.

### Scheduling
Schedule is one of the most important part of the application.

All jobs scheduled in *schedule.tsv*.
The file is scanned by *runner* and its formatting is quite critical.

Main formatting requirements are:
* Each line is a table row.
* Column separator is only a tabulation.
* Last line must be always empty.

When *schedule.tsv* is modified *runner* catches the changes, makes necessary updates and also prints message to the log about that.

To see all scheduled jobs use command *list jobs*:
```
$ python manager.py list jobs

-----------------------------------------------------------------------------------------------------------------------------
|ID |NAME |DESCRIPTION |ENVIRONMENT |FILE                    |MONTH_DAY |WEEK_DAY |HOUR |MINUTE |SECOND |PARAMETERS |STATUS |
-----------------------------------------------------------------------------------------------------------------------------
|0  |test |Test Job    |python      |C:\runner\jobs\0\job.py |*         |*        |8    |0      |0      |           |N      |
-----------------------------------------------------------------------------------------------------------------------------
```
To see only active jobs add *active*.
```
$ python manager.py list jobs active
```

Also you could either open file directly or use command *manager.py edit schedule* to open file using chosen editor in the main config.

#### Schedule Description

|Field name  |Description                                                                                                            |
|------------|-----------------------------------------------------------------------------------------------------------------------|
|ID          |Unique id that job receives automatically during creation.                                                             |
|NAME        |Name of job.                                                                                                           |
|DESCRIPTION |Description of job.                                                                                                    |
|ENVIRONMENT |Name of environment in which job must be executed. All used in *runner* environments must be listed in the main config.|
|FILE        |Entry file. If you use built-in jobs then it is a *job.py*. In other case it is up to you how job should be started.   |
|MONTH_DAY   |Day of month when job must be executed.                                                                                |
|WEEK_DAY    |Day of week when job must be executed.                                                                                 |
|HOUR        |Hour of day when job must be executed.                                                                                 |
|MINUTE      |Minute of our when job must be executed.                                                                               |
|SECOND      |Second of minute when job must be executed.                                                                            |
|PARAMETERS  |Additional arguments that will be passed to FILE in the time of execution.                                             |
|STATUS      |Status of job. Y is an active, N is an inactive.                                                                       |

Job frequency in *runner* is rather flexible.
Be attentive because some combinations can force *runner* to execute job every second!

You could schedule jobs by manipulating with time fields next few ways:
1. Execute job at certain date and time. Use simple integers.
1. Execute job every time cycle. Use integers with symbol */* to point that it is a cycle value.
1. Execute job only during certain period. Use integers with *,* and *-* to point that it is a period value.

For more understanding we list the most popular combinations:

|MONTH_DAY |WEEK_DAY |HOUR |MINUTE |SECOND |When to Execute                        |
|----------|---------|-----|-------|-------|---------------------------------------|
|1         |*        |8    |0      |0      |Each first day of month at 8 am.       |
|*         |1        |8    |0      |0      |Each first day of week at 8 am.        |
|*         |*        |8    |0      |0      |Each day at 8 am.                      |
|*         |*        |/1   |0      |0      |Each hour.                             |
|*         |*        |*    |/5     |0      |Each five minutes.                     |
|*         |1-5      |8    |0      |0      |Each day during weekdays at 8 am.      |
|1,11,21   |*        |8    |0      |0      |Each 1, 11 and 21 day of month at 8 am.|

#### More About Scheduling
Automatic scheduling in *runner* is based on moments.
Moment - is a dynamic scheduler attribute that describes current timestamp as a count of seconds past from era begin.

You can log each scheduler moment if you need to.
For this set the *showtime* option in the *LOG* section of the main config to *True*.
Then in log each moment will be recorded as an empty message:
```
2018-12-31 23:59:59|INFO|
```

Moment includes an active and a passive phases.

Active phase stands for all necessary actions for scheduling and internal *runner* needs.
After active phase finished passive phase begins during which *runner* sleeps till the next step.

If active phase longs more than 1 second in case of some trouble then scheduler internal time will differ from real one.
When this happened *runner* will automatically synchronize moment with real time.
That will be registered in the log that may help in troubleshooting:
```
2018-12-31 23:59:59|WARNING|TIME IS BROKEN!
2018-12-31 23:59:59|INFO|SYNCHRONIZING THE TIME...
2018-12-31 23:59:59|INFO|SUCCESS
```

If you want to log each active phase time consumption then set the *showdelay* option of the *LOG* section in the main config to *True*:

### Tasking
A task is a set of actions that a job must perform.
All tasks must be described in a special job script file.
For our test job this is the file *jobs\0\script.py*.
That file already contains *job* instance so it can be used in the script too.

Open script file or use special command *edit job* that will open it using chosen editor in main config.
```
$ python manager.py edit job 0
```
Modify file as in the example below:
```
> C:\runner\jobs\0\job.py

from job import job

# Write the code to be executed by job down below.
print('Wake up, Neo...')
```
Now go to *schedule.tsv* and change *STATUS* for modified job from *N* to *Y*.

Job is ready and at next 08:00:00 it will be executed.

### Run Job
Job can be executed automatically by scheduler or manually by user.

For automatic execution in *schedule.tsv* must be determined:
1. *ENVIRONMENT* that is a name of environment described in the main config.
1. *MONTH_DAY*, *WEEK_DAY*, *HOUR*, *MINUTE*, *SECOND* - time of execution.

User execution can be done by two ways.

The first one is to use special command *run job* with mandatory arguments *id* and optional argument *trigger*.

Argument *id* is an integer unique identification number of job that can be found in *schedule.tsv*.

Argument *trigger* is a date or datetime in ISO timestamp format for which job must be executed.

In the example below we execute the job with id 0 for 1th January 2019, 8 AM.
```
$ python manager.py run job 0 2019-01-01/08:00:00
INFO: REQUEST TO RUN THE JOB.
INFO: ID: 0.
INFO: NAME: test.
INFO: DESCRIPTION: Test Job.
INFO: TRIGGER: 2019-01-01/08:00:00.
ARE YOU SURE Y/N?
Y
Wake up, Neo...
INFO: DONE.
```

Second one is to execute *job.py* file of the job you want to run.
Following command will execute the job with id 0 for current moment:
```
$ python jobs\0\job.py
Wake up, Neo...
```
Optionally you could use argument -t/--trigger to pass certain date and time.
So execution of job with id 0 for 1th January 2019, 8 AM will looks like:
```
$ python jobs\0\job.py -r 2019-01-01/08:00:00
Wake up, Neo...
```

Also if you have many jobs that must be executed it is possible to use special file.
Let's create file *C:\runner\run_jobs.txt* with listed ids and triggers:
```
0 2018-12-31/08:00:00
0 2019-01-01/08:00:00
```
Note that between id and trigger there is a space.

Execute the command:
```
$ python manager.py run jobs C:\runner\run_jobs.txt
INFO: REQUEST TO RUN THE JOB.
INFO: ID: 0.
INFO: NAME: test.
INFO: DESCRIPTION: Test Job.
INFO: TRIGGER: 2018-12-31/08:00:00.
ARE YOU SURE Y/N?
Y
Wake up, Neo...
INFO: DONE.
********************************************************************************
INFO: REQUEST TO RUN THE JOB.
INFO: ID: 0.
INFO: NAME: test.
INFO: DESCRIPTION: Test Job.
INFO: TRIGGER: 2019-01-01/08:00:00.
ARE YOU SURE Y/N?
Y
Wake up, Neo...
INFO: DONE.
```

### Logging
Logging in *runner* implemented on [logbook](https://github.com/t3eHawk/logbook) and available through the *log* object.
So you could even use *log* in your *script.py*.
```
> C:\runner\jobs\0\script.py

from job import job

# Write the code to be executed by job down below.
print('Wake up, Neo...')
job.log.info('Hello there.')
```
Let's imagine that today is 31th December 2018, 23:59:59.
Run the job and in log file you will see:
```
> C:\runner\jobs\0\logs\test_20181231235959.log

********************************************************************************
*                                                                              *
*          APP: test                                                           *
*         DESC: Test Job                                                       *
*      VERSION: None                                                           *
*    TIMESTAMP: 2018-12-31 23:59:59                                            *
*         FILE: C:\runner\jobs\0\logs\test_20181231235959.log                  *
*      MACHINE: AMD64                                                          *
*    PROCESSOR: Intel64 Family 6 Model 78 Stepping 3, GenuineIntel             *
*     HOSTNAME: Falcon                                                         *
*         USER: Kenobi                                                         *
*    SYSTEM_NM: Windows                                                        *
*   SYSTEM_RLS: 10                                                             *
*   SYSTEM_VER: 10.0.14393                                                     *
*       PYTHON: 3.7.1                                                          *
*           ID: 0                                                              *
*      TRIGGER: 2018-12-31 23:59:59                                            *
*      CONFIGS: C:\runner\jobs\0\config.ini                                    *
*      PERSONS: None                                                           *
*                                                                              *
********************************************************************************
2018-12-31 23:59:59|INFO|JOB STARTED.
2018-12-31 23:59:59|INFO|Hello there.
2018-12-31 23:59:59|INFO|JOB FINISHED.
2018-12-31 23:59:59|INFO|TIME SPENT: 0 seconds.
```
Visit [logbook](https://github.com/t3eHawk/logbook) page to see more features of it.

### Notifications and Alarms
Sometimes in work you may need to get feedback from the job.
It can be easily done with a help of *email* object which allows to write messages on the email.

To use notifier you need SMTP server.
Connection must be defined in config: *ip*, *port*, *user*, *password*, *email address* options of the *[EMAIL]* section in the job config (or other external config).

To send simple text message on the email:
```
> C:\runner\jobs\0\script.py

subject = 'Help me'
text = 'You are my only hope'
recipient = 'ObiWanKenobi@email.com'
job.email.notify(subject, text, recipient)
```

Another case of using notifier is to inform that something went wrong in the job execution.
We use alarms for this purposes in *runner*.
Use *alarm()* to send standard alarm notification on emails listed in the *persons* option of the *[GENERAL]* section in the job config.

Let's change our job with id 0 little bit and execute it.
```
> C:\runner\jobs\0\config.ini
[JOB]
persons = user@email.com
```
```
> C:\runner\jobs\0\script.py
try:
  1/0
except ZeroDivisionError:
  job.log.error()
  job.alarm()
```
As a result you will receive a message on user@email.com:
```
Error occurred during execution.
Job id: 0.
Job name: test.
Job description: Test Job.
Job trigger: 2018-12-31 23:59:59.
Please check the C:\runner\jobs\0\logs\test_20181231235959.log for more details.
```
In *C:\runner\jobs\0\logs\test_20181231235959.log* you will find the error details:
```
2018-12-31 23:59:59|ERROR|FAIL! ERROR: ZeroDivisionError. FILE: C:\runner\jobs\0\script.py. LINE: 7. REASON: division by zero.
```

Visit [notifier](https://github.com/t3eHawk/notifier) page to see more features of it.

### Configuration
You could configure both scheduler and job using configuration files or writing parameters directly to instances constructors.
Remember that direct write to instances has a higher priority than configuration files.

Also you are able to use additional configuration files by passing them through the *config* parameter of *Scheduler* or *Job* instances:

```
scheduler = runner.Scheduler(config = 'C:/configs/myconfig.ini')
# or
job = runner.Job(config = ['C:/configs/myconfig.ini', 'C:/users/Kenobi/myconfig.ini'])
```

But always consider that once you mention these additional configuration files then all parameters from them will be copied to *runner* configuration files.

To edit main configuration file use command *edit config*:
To edit certain job configuration file use command *edit config job 0*.

Options which most likely will be used are already placed to the configuration files.
Below the options descriptions.

|Option       |Section       |Value Example                               |Description                                                           |
|-------------|--------------|--------------------------------------------|----------------------------------------------------------------------|
|editor       |MANAGER       |notepad, nano                               |Text editor used to edit files.                                       |
|name         |SCHEDULER, JOB|scheduler, job_000                          |Name of scheduler or job.                                             |
|desc         |SCHEDULER, JOB|Scheduler, Job 0                            |Description of scheduler or job.                                      |
|schedule     |SCHEDULER     |C:\runner\schedule.tsv, /runner/schedule.tsv|Path to schedule file.                                                |
|console      |LOG           |True, False                                 |Output log to console instead of file.                                |
|limit_by_day |LOG           |True, False                                 |Do we need to close/open log at the start of new day?                 |
|limit_by_size|LOG           |True, False                                 |Do we need to close/open log when maximum size is reached?            |
|max_size     |LOG           |10485760                                    |Maximum size of log.                                                  |
|showtime     |LOG           |True, False                                 |Do we need to see each scheduler moment in log?                       |
|showdelay    |LOG           |True, False                                 |Do we need to see scheduler active phases time consumptions in log?   |
|python       |ENVIRONMENT   |python, python3                             |Path or command to Python executable.                                 |
|cpp          |ENVIRONMENT   |cpp                                         |Path or command to C++ executable.                                    |
|java         |ENVIRONMENT   |java                                        |Path or command to Java executable.                                   |
|persons      |JOB           |ObiWanKenobi@email.com                      |Email address (one or more) who receives job notifications and alarms.|
|ip           |EMAIL         |127.0.0.1                                   |Ip address of host with SMTP server.                                  |
|port         |EMAIL         |587                                         |Port of STMP server.                                                  |
|need_login   |EMAIL         |True, False                                 |Do we need to login to SMTP server?                                   |
|user         |EMAIL         |Kenobi                                      |Username to login.                                                    |
|password     |EMAIL         |4mayBeWithYou                               |Password to login.                                                    |
|address      |EMAIL         |LukeSkywalker@email.com                     |Email address that sends job notifications and alarms.                |
|need_debug   |EMAIL         |True, False                                 |Do we need to see details of connection process?                      |
|need_tls     |EMAIL         |True, False                                 |Do we need to cover connection to SMTP with TLS protocol?             |

#### More About Environments
In *runner* you could add any environments for job execution.
Let's example on Python virtual environment *venv*:
```
$ python -m venv C:\runner\venv
```
That will deploy Python virtual environment right in the folder with our runner application.

Open main config and add to the *ENVIRONMENT* section a new option with the path to the deployed *venv* main executable:
```
[ENVIRONMENT]
<...>
venv = C:\runner\venv\scripts\python.exe
```
Then change in the schedule the *ENVIRONMENT* for the test job from *python* picked during the creation to *venv*.

Now your job will be handled by virtual Python copy, so *pip install* any modules you need and feel your self free.

---
For information about constructors attributes refer to the technical documentation.

For details of external module objects go to appropriate page with this module documentation.

## Tests
You could find tests for Windows and Linux in /test.

## Issues
To report about found bugs and problems refer to [issues](https://github.com/t3eHawk/runner/issues)

## Uninstall
To uninstall just delete folder your/python/folder/Lib/site-packages/runner.
