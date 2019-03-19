import re
import time

class Trigger():
    def __init__(self, scheduler):
        self.scheduler = scheduler
        pass

    def scan(self):
        now = time.localtime(self.scheduler.moment)
        compare = self.compare
        for job in self.scheduler.schedule:
            if job['status'] == 'Y':
                if compare(job['month_day'], now.tm_mday) is True:
                    if compare(job['week_day'], now.tm_wday) is True:
                        if compare(job['hour'], now.tm_hour) is True:
                            if compare(job['minute'], now.tm_min) is True:
                                if compare(job['second'], now.tm_sec) is True:
                                    self.pull(job)

    def compare(self, unit, now):
        # Check if empty or *.
        if re.match(r'^(\*)$', unit) is not None:
            return True
        # Check if unit is lonely digit and equals to now.
        elif re.match(r'^\d+$', unit) is not None:
            unit = int(unit)
            return True if now == unit else False
        # Check if unit is a cycle and integer division with now is true.
        elif re.match(r'^/\d+$', unit) is not None:
            unit = int(re.search(r'\d+', unit).group())
            if unit == 0: return False
            return True if now % unit == 0 else False
        # Check if unit is a range and now is in this range.
        elif re.match(r'^\d+-\d+$', unit):
            unit = [int(i) for i in re.findall(r'\d+', unit)]
            return True if now in range(unit[0], unit[1] + 1) else False
        # Check if unit is a list and now is in this list.
        elif re.match(r'^\d+,\s*\d+.*$', unit):
            unit = [int(i) for i in re.findall(r'\d+', unit)]
            return True if now in unit else False
        # All other cases is not for the now.
        else:
            return False

    def pull(self, job):
        log = self.scheduler.log
        config = self.scheduler.config
        operator = self.scheduler.operator
        try:
            id = job['id']
            env = job['environment']
            file = job['file']
            params = job['parameters']
            params += ' -a'
            exe = config['ENVIRONMENT'].get(env)
            log.info(f'CREATING SUBPROCESS FOR JOB {id}...')
            # Job will run as separate process.
            operator.make_process(exe, file, params)
        except:
            log.error(f'SUBPROCESS FOR JOB {id} WAS NOT CREATED')
            log.error()
        else:
            log.info(f'SUBPROCESS FOR JOB {id} WAS CREATED SUCCESSFULLY')
        pass
