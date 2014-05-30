import mock
import pyconfig
import pymongo

from unittest.case import SkipTest

from ..util import *
from humbledb import Mongo
from humbledb import _version


def teardown():
    DBTest.authenticate(database_name(), username='authuser', password='pass1')
    DBTest.connection[database_name()].drop_collection('test')


def test_new():
    assert_equal(DBTest, DBTest())


@raises(TypeError)
def test_missing_config_host():
    class Test(Mongo):
        config_port = 27017


def test_missing_config_port():
    class Test(Mongo):
        config_host = 'localhost'

    eq_(Test.config_port, None)

    # pymongo will default to use port 27017 if no port is given
    with Test:
        eq_(Test.connection.port, 27017)


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


