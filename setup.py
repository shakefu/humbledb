import multiprocessing, logging # Fix atexit bug
from setuptools import setup, find_packages

import humbledb

setup(
        name='humbledb',
        version=humbledb.__version__,
        description="HumbleDB - MongoDB Object-Document Mapper",
        author="Jacob Alheid",
        author_email="jake@about.me",
        packages=find_packages(exclude=['test']),
        install_requires=[
            'pymongo >= 2.2.1',
            'pyconfig',
            'pytool',
            ],
        test_suite='nose.collector',
        tests_require=[
            'nose',
            'mock',
            ],
        )

