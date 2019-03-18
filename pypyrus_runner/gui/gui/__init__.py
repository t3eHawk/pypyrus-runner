from pyramid.config import Configurator

def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.include('.routes')
    config.include('.static')
    config.scan('.views')
    return config.make_wsgi_app()
