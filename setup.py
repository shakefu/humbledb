from setuptools import setup, find_packages


def version():
    try:
        import re
        return re.search("^__version__ = '(.*)'",
                open('humbledb/__init__.py').read(), re.M).group(1)
    except:
        raise RuntimeError("Could not get version")


setup(
        name='humbledb',
        version=version(),
        description="HumbleDB - MongoDB Object-Document Mapper",
        author="Jacob Alheid",
        author_email="jake@about.me",
        packages=find_packages(exclude=['test']),
        install_requires=[
            'pymongo >= 2.0.1',
            'pyconfig',
            'pytool >= 3.4.1',
            'six',
            ],
        test_suite='nose.collector',
        tests_require=[
            'nose',
            'mock',
            ],
        )

