import multiprocessing, logging # Fix atexit bug
from setuptools import setup, find_packages

setup(
        name='aboutme-db',
        version='1.1.0',
        description="About.me Database Utilities (MongoDB)",
        author="Jacob Alheid",
        author_email="jake@about.me",
        packages=find_packages(exclude=['test']),
        namespace_packages=['me'],
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

