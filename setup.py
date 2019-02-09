import setuptools
import pypyrus_runner as runner

with open('README.md', 'r') as fh:
    long_description = fh.read()

author = runner.__author__
email = runner.__email__
version = runner.__version__
description = runner.__doc__
license = runner.__license__

setuptools.setup(
    name='pypyrus-runner',
    version=version,
    author=author,
    author_email=email,
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    license=license,
    url='https://github.com/t3eHawk/runner',
    install_requires=['pypyrus-tables>=0.0.2', 'pypyrus-logbook>=0.0.2'],
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
