import mock
import pymongo
import pyconfig

from ..util import *
from humbledb import Mongo


def teardown():
    DBTest.connection.drop_database(database_name())


def test_new():
    assert_equal(DBTest, DBTest())


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


def test_replica():
    try:
        with mock.patch('pymongo.ReplicaSetConnection') as replica:
            class Replica(Mongo):
                config_host = 'localhost'
                config_port = 27017
                config_replica = 'test'

            with Replica:
                pass

            replica.assert_called_once()
    except AttributeError, exc:
        if pymongo.version < '2.1':
            ok_('ReplicaSetConnection' in exc.message)
        else:
            raise


def test_reconnect():
    with mock.patch.object(DBTest, '_new_connection') as _new_conn:
        DBTest.reconnect()
        _new_conn.assert_called_once()

    # Have to reconnect again to get real connection instance back
    DBTest.reconnect()


@mock.patch('pymongo.ReplicaSetConnection')
def test_config_replica_creates_replica_set_connection(conn):
    class MyReplica(Mongo):
        config_host = 'localhost'
        config_port = 27017
        config_replica = 'MyReplica'

    with MyReplica:
        pass

    conn.assert_called_once()
