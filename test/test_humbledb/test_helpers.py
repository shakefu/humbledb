"""
Tests for Helpers
=================

"""
import pyconfig

from humbledb import _version
from humbledb import Document, Mongo
from humbledb.helpers import auto_increment
from humbledb.errors import DatabaseMismatch, NoConnection
from ..util import DBTest, database_name, eq_, raises, SkipTest


SIDECAR = 'sidecars'


class MyDoc(Document):
    config_database = database_name()
    config_collection = 'test'

    auto = 'a', auto_increment(database_name(), SIDECAR, 'MyDoc')


def teardown():
    pass


def test_auto_increment_works_as_advertised():
    doc = MyDoc()
    with DBTest:
        MyDoc.save(doc, safe=True)

    eq_(doc.auto, 1)

    doc = MyDoc()
    with DBTest:
        eq_(doc.auto, 2)
        MyDoc.save(doc)

    eq_(doc.auto, 2)


@raises(DatabaseMismatch)
def test_auto_increment_errors_with_wrong_db():
    if _version._lt('2.6.0'):
        raise SkipTest

    host = pyconfig.get('humbledb.test.db.host', 'localhost')
    port = pyconfig.get('humbledb.test.db.port', 27017)
    uri = 'mongodb://{}:{}/{}'.format(host, port, database_name())

    class DBuri(Mongo):
        config_uri = uri

    class MyDoc2(Document):
        config_database = database_name()
        config_collection = 'test'

        auto = 'a', auto_increment(database_name() + '_is_different', SIDECAR,
                'MyDoc2')


    doc = MyDoc2()
    with DBuri:
        doc.auto


@raises(NoConnection)
def test_autoincrement_requires_connection():
    doc = MyDoc()
    doc.auto


