import logging
import re
from unittest.case import SkipTest

import pyconfig

import humbledb
from humbledb import Mongo

__all__ = [
    "assert_is_subclass",
    "is_subclass_",
    "assert_is",
    "is_",
    "SkipTest",
    "database_name",
    "DBTest",
    # "enable_sharding",
]


def database_name():
    """Return the test database name."""
    return pyconfig.get("humbledb.test.db.name", "humbledb_test")


def old_enable_sharding(collection, key):
    """Enable sharding for `collection`."""
    conn = DBTest.connection
    try:
        conn.admin.command("listShards")
    except humbledb.errors.OperationFailure as exc:
        if re.match(".*no such.*listShards", str(exc)):
            logging.getLogger(__name__).info("Sharding not available.")
            return False
        raise
    try:
        conn.admin.command("enableSharding", database_name())
    except humbledb.errors.OperationFailure as exc:
        if "already" not in str(exc):
            raise
    try:
        conn.admin.command(
            "shardCollection", database_name() + "." + collection, key=key
        )
    except humbledb.errors.OperationFailure as exc:
        if "already" not in str(exc):
            raise
    logging.getLogger(__name__).info(
        "Sharding enabled for %r.%r on %r.", database_name(), collection, key
    )
    return True


class DBTest(Mongo):
    config_host = pyconfig.setting("humbledb.test.db.host", "localhost")
    config_port = pyconfig.setting("humbledb.test.db.port", 27017)


def assert_is_subclass(obj, cls):
    """Assert an object is a subclas of another."""
    assert issubclass(obj, cls), "{!r} is not a subclass of {!r}".format(obj, cls)


# Shortcut alias
is_subclass_ = assert_is_subclass


def assert_is(obj1, obj2):
    """Assert an object is identical (same object)."""
    assert obj1 is obj2, "{!r} is not {!r}".format(obj1, obj2)


# Shortcut alias
is_ = assert_is
