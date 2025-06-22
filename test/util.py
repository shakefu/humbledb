from unittest.case import SkipTest

import pyconfig

__all__ = [
    "assert_is_subclass",
    "is_subclass_",
    "assert_is",
    "is_",
    "SkipTest",
    "database_name",
]


def database_name():
    """Return the test database name."""
    return pyconfig.get("humbledb.test.db.name", "humbledb_test")


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
