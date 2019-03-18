def includeme(config):
    config.add_route('schedule', '/')
    config.add_route('history', '/history')
    config.add_route('jobs', '/jobs')
    config.add_route('logs', '/logs')
    config.add_route('settings', '/settings')
    config.add_route('test', '/test')
    pass
