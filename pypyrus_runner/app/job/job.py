import pypyrus_runner as runner

if __name__ == '__main__':
    import script
else:
    job = runner.Job()
    job.push()
