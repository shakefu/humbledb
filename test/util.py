import pyconfig
import nose.tools

from humbledb import Mongo


__all__ = [
        'eq_',
        'ok_',
        'raises',
        'assert_equal',
        'assert_is_instance',
        'is_instance_',
        'assert_is_subclass',
        'is_subclass_',
        'assert_is',
        'is_',
        'database_name',
        'DBTest',
        ]


eq_ = nose.tools.eq_
ok_ = nose.tools.ok_
raises = nose.tools.raises
assert_equal = nose.tools.assert_equal
assert_is_instance = nose.tools.assert_is_instance
is_instance_ = assert_is_instance


def database_name():
    return pyconfig.get('humbledb.test.db.name', 'nose_humbledb')


# These names have to start with an underscore so nose ignores them, otherwise
# it raises an error when trying to run the tests
class DBTest(Mongo):
    config_host = pyconfig.setting('humbledb.test.db.host', 'localhost')
    config_port = pyconfig.setting('humbledb.test.db.port', 27017)


# This instantiates the connection and causes nose to crap out if there's no
# database available, which is what we want
try:
    with DBTest:
        pass
except:
    raise RuntimeError("Cannot connect to database.")


def assert_is_subclass(obj, cls):
    """ Additional assertion helper. """
    assert issubclass(obj, cls), "{!r} is not a subclass of {!r}".format(obj,
            cls)

is_subclass_ = assert_is_subclass


def assert_is(obj1, obj2):
    assert obj1 is obj2, "{!r} is not {!r}".format(obj1, obj2)

is_ = assert_is
