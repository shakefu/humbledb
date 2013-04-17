import multiprocessing, logging # Fix atexit bug
from setuptools import setup, find_packages

exec("c=__import__('compiler');a='__version__';l=[];g=lambda:[n.expr.value for"
        " n in l for o in n.nodes if o.name==a].pop();c.walk(c.parseFile('%s/_"
        "_init__.py'),type('v',(object,),{'visitAssign':lambda s,n:l.append(n)"
        "})());exec(a+'=g()');"%'humbledb')

setup(
        name='humbledb',
        version=__version__,
        description="HumbleDB - MongoDB Object-Document Mapper",
        author="Jacob Alheid",
        author_email="jake@about.me",
        packages=find_packages(exclude=['test']),
        install_requires=[
            'pymongo >= 2.0.1',
            'pyconfig',
            'pytool >= 3.0.1',
            ],
        test_suite='nose.collector',
        tests_require=[
            'nose',
            'mock',
            ],
        )

