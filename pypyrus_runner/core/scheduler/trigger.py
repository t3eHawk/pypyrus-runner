import re

class Trigger():
    def __init__(self, scheduler):
        self._scheduler = scheduler
        self.log = scheduler.log
        pass

    def charge(self, unit, now):
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
        try:
            id = job['id']
            env = job['environment']
            file = job['file']
            params = job['parameters']
            params += ' -a'
            exe = self._scheduler.config['ENVIRONMENT'].get(env)
            self.log.info(f'CREATING SUBPROCESS FOR JOB {id}...')
            # Job will run as separate process.
            self._scheduler.operator.make_process(exe, file, params)
        except:
            self.log.error(f'SUBPROCESS FOR JOB {id} WAS NOT CREATED')
            self.log.error()
        else:
            log.info(f'SUBPROCESS FOR JOB {id} WAS CREATED SUCCESSFULLY')
        pass
