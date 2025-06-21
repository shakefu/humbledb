"""
Tests for Helpers
=================

"""

import pyconfig
import pytest

from humbledb import Document, Mongo, _version
from humbledb.errors import DatabaseMismatch, NoConnection
from humbledb.helpers import auto_increment

from ..util import DBTest, SkipTest, database_name

SIDECAR = "sidecars"


# The safe= keyword doesn't exist in 3.0
if _version._lt("3.0.0"):
    _safe = {"safe": True}
else:
    _safe = {}


class MyDoc(Document):
    config_database = database_name()
    config_collection = "test"

    auto = "a", auto_increment(database_name(), SIDECAR, "MyDoc")


class MyFloatCounterDoc(Document):
    config_database = database_name()
    config_collection = "float_test"

    auto = "a", auto_increment(database_name(), SIDECAR, "FloatDoc")


class BigCounterDoc(Document):
    config_database = database_name()
    config_collection = "big_doc"

    auto = "a", auto_increment(database_name(), SIDECAR, "BigCounterDoc", increment=10)


def setup():
    # Set up a float counter in the sidecar collection.
    import pymongo

    if _version._gte("2.4"):
        conn = pymongo.MongoClient("127.0.0.1")
    else:
        conn = pymongo.Connection("127.0.0.1")
    coll = conn[database_name()][SIDECAR]
    coll.insert({"_id": "FloatDoc", "value": float(100)})


def teardown():
    pass


def test_auto_increment_works_as_advertised():
    doc = MyDoc()
    with DBTest:
        MyDoc.save(doc, **_safe)

    # Counters are expected to be integers.
    assert isinstance(doc.auto, int)
    assert doc.auto == 1

    doc = MyDoc()
    with DBTest:
        assert doc.auto == 2
        MyDoc.save(doc)

    assert isinstance(doc.auto, int)
    assert doc.auto == 2


def test_auto_increment_initial_float_counter_value_remains_a_float():
    if _version._gte("4.0"):
        pytest.skip("Pymongo 4.x / Python 3.x changed the float consistency behavior")

    doc = MyFloatCounterDoc()
    with DBTest:
        MyFloatCounterDoc.save(doc, **_safe)

    # There are instances where the counters can be initialized
    # as MongoDB Double types.
    assert isinstance(doc.auto, float)

    assert doc.auto == 101  # Floats can pass as integers
    assert doc.auto == 101.0  # But are really floats

    assert str(doc.auto) == "101.0"  # And will output as floats.
    assert str(doc.auto) != "101"  # Not as integers.

    doc = MyFloatCounterDoc()
    with DBTest:
        assert doc.auto == 102.0
        MyFloatCounterDoc.save(doc, **_safe)

    assert isinstance(doc.auto, float)
    assert doc.auto == 102
    assert doc.auto == 102.0


def test_auto_increment_works_with_user_defined_increment_step():
    doc = BigCounterDoc()
    with DBTest:
        BigCounterDoc.save(doc, **_safe)

    assert doc.auto == 10

    doc = BigCounterDoc()
    with DBTest:
        assert doc.auto == 20
        BigCounterDoc.save(doc)

    assert doc.auto == 20


def test_auto_increment_errors_with_wrong_db():
    if _version._lt("2.6.0"):
        raise SkipTest

    host = pyconfig.get("humbledb.test.db.host", "localhost")
    port = pyconfig.get("humbledb.test.db.port", 27017)
    uri = "mongodb://{}:{}/{}".format(host, port, database_name())

    class DBuri(Mongo):
        config_uri = uri

    class MyDoc2(Document):
        config_database = database_name()
        config_collection = "test"

        auto = "a", auto_increment(database_name() + "_is_different", SIDECAR, "MyDoc2")

    doc = MyDoc2()
    with pytest.raises(DatabaseMismatch):
        with DBuri:
            doc.auto


def test_autoincrement_requires_connection():
    doc = MyDoc()
    with pytest.raises(NoConnection):
        doc.auto
