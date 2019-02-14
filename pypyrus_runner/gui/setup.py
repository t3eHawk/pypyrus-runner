import setuptools

install_requires = ['pyramid', 'pyramid_chameleon', 'waitress']
dev_requires = ['pyramid_debugtoolbar']
extras_require = {'dev': dev_requires}
entry_points = {'paste.app_factory': ['main = gui:main']}

setuptools.setup(
    name='pypyrus-runner-gui',
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points=entry_points,
)
