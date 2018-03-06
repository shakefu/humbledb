import re
import logging
import pyconfig
import nose.tools
from unittest.case import SkipTest

import humbledb
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
        'SkipTest',
        'database_name',
        'DBTest',
        'enable_sharding',
        ]


# Shortcut aliases for nose imports
eq_ = nose.tools.eq_
ok_ = nose.tools.ok_
raises = nose.tools.raises
assert_equal = nose.tools.assert_equal
assert_is_instance = nose.tools.assert_is_instance
is_instance_ = assert_is_instance


def database_name():
    """ Return the test database name. """
    return pyconfig.get('humbledb.test.db.name', 'nose_humbledb')


def enable_sharding(collection, key):
    """ Enable sharding for `collection`. """
    conn = DBTest.connection
    try:
        conn.admin.command('listShards')
    except humbledb.errors.OperationFailure, exc:
        if re.match('.*failed: no such.*listShards', exc.message):
            logging.getLogger(__name__).info("Sharding not available.")
            return False
        raise
    try:
        conn.admin.command('enableSharding', database_name())
    except humbledb.errors.OperationFailure, exc:
        if 'failed: already' not in exc.message:
            raise
    try:
        conn.admin.command('shardCollection', database_name() + '.' +
                collection, key=key)
    except humbledb.errors.OperationFailure, exc:
        if 'failed: already' not in exc.message:
            raise
    logging.getLogger(__name__).info("Sharding enabled for %r.%r on %r.",
            database_name(), collection, key)
    return True


class DBTest(Mongo):
    config_host = pyconfig.setting('humbledb.test.db.host', 'localhost')
    config_port = pyconfig.setting('humbledb.test.db.port', 27017)


# This instantiates the connection and causes nose to crap out if there's no
# database available, which is what we want
with DBTest:
    logging.getLogger(__name__).info("Connection successful.")


def assert_is_subclass(obj, cls):
    """ Assert an object is a subclas of another. """
    assert issubclass(obj, cls), "{!r} is not a subclass of {!r}".format(obj,
            cls)

# Shortcut alias
is_subclass_ = assert_is_subclass


def assert_is(obj1, obj2):
    """ Assert an object is identical (same object). """
    assert obj1 is obj2, "{!r} is not {!r}".format(obj1, obj2)

# Shortcut alias
is_ = assert_is
