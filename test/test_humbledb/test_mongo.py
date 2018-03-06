import mock
import pyconfig
from unittest.case import SkipTest

from humbledb import Mongo, Document, _version
from humbledb.errors import DatabaseMismatch, ConnectionFailure
from ..util import database_name, ok_, eq_, DBTest, raises


def teardown():
    DBTest.connection.drop_database(database_name())


def test_new():
    eq_(DBTest, DBTest())


@raises(TypeError)
def test_missing_config_host():
    class Test(Mongo):
        config_port = 27017


@raises(TypeError)
def test_missing_config_port():
    class Test(Mongo):
        config_host = 'localhost'


def test_reload():
    with mock.patch.object(DBTest, '_new_connection') as _new_conn:
        pyconfig.reload()
        _new_conn.assert_called_once()

    # Have to reload again to get real connection instance back
    pyconfig.reload()


@raises(RuntimeError)
def test_nested_conn():
    with DBTest:
        with DBTest:
            pass


def test_harmless_end():
    # This shouldn't raise any errors
    DBTest.end()
    DBTest.start()
    DBTest.end()
    DBTest.end()


def test_replica_works_for_versions_between_2_1_and_2_4():
    if _version._lt('2.1') or _version._gte('2.4'):
        raise SkipTest

    with mock.patch('pymongo.ReplicaSetConnection') as replica:
        class Replica(Mongo):
            config_host = 'localhost'
            config_port = 27017
            config_replica = 'test'

        with Replica:
            pass

        replica.assert_called_once()


def test_replica_works_for_versions_after_2_4():
    if _version._lt('2.4'):
        raise SkipTest

    if _version._gte('3'):
        raise SkipTest

    with mock.patch('pymongo.MongoReplicaSetClient') as replica:
        class Replica(Mongo):
            config_host = 'localhost'
            config_port = 27017
            config_replica = 'test'

        with Replica:
            pass

        replica.assert_called_once()


@raises(TypeError)
def test_replica_errors_for_versions_before_2_1():
    if _version._gte('2.1'):
        raise SkipTest

    class Replica(Mongo):
        config_host = 'localhost'
        config_port = 27017
        config_replica = 'test'


def test_reconnect():
    with mock.patch.object(DBTest, '_new_connection') as _new_conn:
        DBTest.reconnect()
        _new_conn.assert_called_once()

    # Have to reconnect again to get real connection instance back
    DBTest.reconnect()


def test_mongo_uri_with_database():
    if _version._lt('2.6.0'):
        raise SkipTest("Needs version 2.6.0 or later")

    host = pyconfig.get('humbledb.test.db.host', 'localhost')
    port = pyconfig.get('humbledb.test.db.port', 27017)
    uri = 'mongodb://{}:{}/{}'.format(host, port, database_name())

    class DBuri(Mongo):
            config_uri = uri

    with DBuri:
        eq_(DBuri.database.name, database_name())
        eq_(Mongo.context.database.name, database_name())


@raises(DatabaseMismatch)
def test_mongo_uri_database_with_conflict_raises_error():
    if _version._lt('2.6.0'):
        raise SkipTest("Needs version 2.6.0 or later")

    host = pyconfig.get('humbledb.test.db.host', 'localhost')
    port = pyconfig.get('humbledb.test.db.port', 27017)
    uri = 'mongodb://{}:{}/{}'.format(host, port, database_name())

    class DBuri(Mongo):
            config_uri = uri

    from humbledb import Document
    class TestDoc(Document):
        config_database = database_name() + '_is_different'
        config_collection = 'test'

    with DBuri:
        TestDoc.find()


@raises(TypeError)
def test_mongo_client_with_ssl_before_2_1():
    if _version._gte('2.1'):
        raise SkipTest("Only test this with version 2.1 or earlier.")

    class SSLMongo(Mongo):
        config_host = 'localhost'
        config_port = 27017
        config_ssl = True


def test_mongo_client_with_ssl_after_2_1():
    if _version._lt('2.1'):
        raise SkipTest("This test requires version 2.1 or later.")

    class SSLMongo(Mongo):
        config_host = 'localhost'
        config_port = 27017
        config_ssl = True
        config_mongo_client = ({'serverSelectionTimeoutMS': 300} if
                _version._gte('3.0') else {})

    class SomeDoc(Document):
        config_database = database_name()
        config_collection = 'ssl_collection'

        name = 'n'

    try:
        SomeDoc.insert
    except:
        raise

    try:
        import socket
        socket.setdefaulttimeout(3)
        with SSLMongo:
            SomeDoc.insert({SomeDoc.name:'foobar'})
            ok_(SomeDoc.find({SomeDoc.name:'foobar'}))
    except ConnectionFailure as err:
        raise SkipTest("SSL may not be enabled on mongodb server: %r" % err)


