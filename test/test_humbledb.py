import mock
import pyconfig

from .util import *
from humbledb import Mongo, Document


DB_NAME = 'nose_test'


# These names have to start with an underscore so nose ignores them, otherwise
# it raises an error when trying to run the tests
class _TestDB(Mongo):
    config_host = 'localhost'
    config_port = 27017


class _TestDoc(Document):
    config_database = DB_NAME
    config_collection = 'test_doc'

    user_name = 'u'


def test_new():
    assert_equal(_TestDB, _TestDB())


def test_delete():
    n = _TestDoc()
    n.user_name = 'test'
    ok_(_TestDoc.user_name in n)
    del n.user_name
    eq_(_TestDoc.user_name in n, False)


@raises(RuntimeError)
def test_without_context():
    _TestDoc.find_one()


@raises(TypeError)
def test_bad_name():
    class Test(Document):
        items = 'i'


@raises(TypeError)
def test_missing_database():
    class Test(Document):
        pass


@raises(TypeError)
def test_missing_collection():
    class Test(Document):
        config_database = DB_NAME


@raises(AttributeError)
def test_bad_attribute():
    with _TestDB:
        _TestDoc.foo


def test_ignore_method():
    class Test(Document):
        config_database = DB_NAME
        config_collection = 'test'
        def test(self):
            pass

    ok_(callable(Test.test))


def test_unmapped_fields():
    n = _TestDoc(foo='bar')
    ok_('foo' in n)
    eq_(n['foo'], 'bar')
    ok_('foo' in n._asdict())
    eq_(n._asdict()['foo'], 'bar')


@raises(TypeError)
def test_missing_config_host():
    class Test(Mongo):
        config_port = 27017


@raises(TypeError)
def test_missing_config_port():
    class Test(Mongo):
        config_host = 'localhost'


def test_reload():
    with mock.patch.object(_TestDB, '_new_connection') as _new_conn:
        pyconfig.reload()
        _new_conn.assert_called_once()

    # Have to reload again to get real connection instance back
    pyconfig.reload()


@raises(RuntimeError)
def test_nested_conn():
    with _TestDB:
        with _TestDB:
            pass


def test_harmless_end():
    # This shouldn't raise any errors
    _TestDB.end()
    _TestDB.start()
    _TestDB.end()
    _TestDB.end()


def test_instance_dictproxy_attr():
    _doc = _TestDoc()
    _doc.user_name = 'value'
    eq_(_doc.user_name, 'value')
    eq_(_TestDoc().user_name, None)


def test_ensure_indexes_called():
    class Test(Document):
        config_database = DB_NAME
        config_collection = 'test'
        config_indexes = ['user_name']

        user_name = 'u'

    with _TestDB:
        with mock.patch.object(Test, '_ensure_indexes') as _ensure:
            eq_(Test._ensure_indexes, _ensure)
            Test.ensured = None
            Test.find_one()
            _ensure.assert_called_once()


def test_ensure_indexes_calls_ensure_index():
    class Test(Document):
        config_database = DB_NAME
        config_collection = 'test'
        config_indexes = ['user_name']

        user_name = 'u'

    with _TestDB:
        with mock.patch.object(Test, 'collection') as coll:
            coll.find_one.__name__ = 'find_one'
            Test.ensured = None
            Test.find_one()
            coll.ensure_index.assert_called_with(
                    Test.user_name,
                    background=True,
                    ttl=60*60*24)


def test_ensure_indexes_reload_hook():
    class Test(Document):
        config_database = DB_NAME
        config_collection = 'test'
        config_indexes = ['user_name']

        user_name = 'u'

    with _TestDB:
        Test.find_one()

    eq_(Test.ensured, True)
    pyconfig.reload()
    eq_(Test.ensured, False)


def test_wrap_methods():
    with _TestDB:
        with mock.patch.object(_TestDoc, '_wrap') as _wrap:
            _wrap.return_value = '_wrapper'
            eq_(_TestDoc.find, _wrap.return_value)
            _wrap.assert_called_once()


def test_wrap_method_has_as_class():
    with _TestDB:
        with mock.patch.object(_TestDoc, 'collection') as coll:
            coll.find.__name__ = 'find'
            _TestDoc.find()
            coll.find.assert_called_with(as_class=_TestDoc)


def test_update_passthrough():
    with _TestDB:
        eq_(_TestDoc.collection.update, _TestDoc.update)


def test_document_repr():
    # Coverage all the coverage!
    d = {'foo': 'bar'}
    eq_(repr(_TestDoc(d)), "_TestDoc({})".format(repr(d)))


def test_asdict():
    eq_(_TestDoc({'u': 'test_name'})._asdict(), {'user_name': 'test_name'})


@mock.patch('pymongo.ReplicaSetConnection')
def test_replica(replica):
    class Replica(Mongo):
        config_host = 'localhost'
        config_port = 27017
        config_replica = 'test'

    with Replica:
        pass

    replica.assert_called_once()


def test_reconnect():
    with mock.patch.object(_TestDB, '_new_connection') as _new_conn:
        _TestDB.reconnect()
        _new_conn.assert_called_once()

    # Have to reconnect again to get real connection instance back
    _TestDB.reconnect()


