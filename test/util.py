import pyconfig
import nose.tools

from humbledb import Mongo


__all__ = [
        'eq_',
        'ok_',
        'raises',
        'assert_equal',
        'assert_is_instance',
        'database_name',
        'DBTest',
        ]


eq_ = nose.tools.eq_
ok_ = nose.tools.ok_
raises = nose.tools.raises
assert_equal = nose.tools.assert_equal
assert_is_instance = nose.tools.assert_is_instance


def database_name():
    return pyconfig.get('humbledb.test.db.name', 'nose_humbledb')


# These names have to start with an underscore so nose ignores them, otherwise
# it raises an error when trying to run the tests
class DBTest(Mongo):
    config_host = pyconfig.setting('humbledb.test.db.host', 'localhost')
    config_port = pyconfig.setting('humbledb.test.db.port', 27017)


