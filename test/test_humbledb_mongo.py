import mock
import pytool
import pyconfig

from .util import *
from humbledb import Mongo, Document, Embed


DB_NAME = 'humbledb_nosetest'


# These names have to start with an underscore so nose ignores them, otherwise
# it raises an error when trying to run the tests
class _TestDB(Mongo):
    config_host = 'localhost'
    config_port = 27017


class _TestDoc(Document):
    config_database = DB_NAME
    config_collection = 'test_doc'

    user_name = 'u'


class EmbedTestDoc(Document):
    attr = 'a'
    attr2 = 'a2'

    embed = Embed('e')
    embed.attr = 'a'

    embed.embed = Embed('e')
    embed.embed.attr = 'a'


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


@raises(RuntimeError)
def test_missing_database():
    class Test(Document):
        config_collection = 'test'

    with _TestDB:
        Test.collection


@raises(RuntimeError)
def test_missing_collection():
    class Test(Document):
        config_database = DB_NAME

    with _TestDB:
        Test.collection


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
            Test._ensured = None
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
            Test._ensured = None
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

    eq_(Test._ensured, True)
    pyconfig.reload()
    eq_(Test._ensured, False)


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



def test_nonstring():
    _instance = object()
    class _TestNonString(Document):
        config_database = DB_NAME
        config_collection = 'test'

        foo = 2
        bar = True
        cls = object
        instance = _instance
        ok = 'OK'

    eq_(_TestNonString._name_map.filtered(), {'ok': 'OK'})
    eq_(_TestNonString.foo, 2)
    eq_(_TestNonString.bar, True)
    eq_(_TestNonString.cls, object)
    eq_(_TestNonString.instance, _instance)
    eq_(_TestNonString.ok, 'OK')
    eq_(_TestNonString().foo, 2)
    eq_(_TestNonString().bar, True)
    eq_(_TestNonString().cls, object)
    eq_(_TestNonString().instance, _instance)
    eq_(_TestNonString().ok, None)


def test_property_attribute():
    class _TestProperty(Document):
        config_database = DB_NAME
        config_collection = 'test'

        @property
        def attr(self):
            return self

        foo = 'bar'

    eq_(_TestProperty._name_map.filtered(), {'foo': 'bar'})
    tp = _TestProperty()
    eq_(tp.attr, tp)


def test_inheritance():
    class _TestDoc2(_TestDoc):
        pass

    eq_(_TestDoc2.user_name, _TestDoc.user_name)
    eq_(_TestDoc2.config_database, _TestDoc.config_database)
    eq_(_TestDoc2.config_collection, _TestDoc.config_collection)

    # This is to ensure the collection is accessible, e.g. not raising an error
    with _TestDB:
        _TestDoc2.collection


def test_inheritance_combined():
    class _TestDoc2(_TestDoc):
        new_name = 'n'

    eq_(_TestDoc2.new_name, 'n')
    eq_(_TestDoc2.user_name, _TestDoc.user_name)


def test_classproperty_attribute():
    class _TestClassProp(Document):
        config_database = DB_NAME
        config_collection = 'test'

        @pytool.lang.classproperty
        def attr(cls):
            return cls

    eq_(_TestClassProp.attr, _TestClassProp)
    eq_(_TestClassProp().attr, _TestClassProp)


def test_self_insertion():
    # This sounds dirty
    t = _TestDoc()
    with _TestDB:
        type(t).insert(t)

    ok_(t._id)


@raises(AttributeError)
def test_collection_attributes_not_accessible_from_instance():
    t = _TestDoc()
    with _TestDB:
        t.find


def test_collection_accessible_from_instance():
    t = _TestDoc()
    with _TestDB:
        t.collection


def test_attr():
    eq_(EmbedTestDoc.attr, 'a')


def test_embed():
    eq_(EmbedTestDoc.embed, 'e')


def test_embed_attr():
    eq_(EmbedTestDoc.embed.attr, 'e.a')


def test_embed_embed():
    eq_(EmbedTestDoc.embed.embed, 'e.e')


def test_embed_embed_attr():
    eq_(EmbedTestDoc.embed.embed.attr, 'e.e.a')


def test_instance_attr():
    t = EmbedTestDoc()
    t['a'] = 'hello'
    eq_(t.attr, 'hello')


def test_instance_embed_attr():
    t = EmbedTestDoc()
    t['e'] = {}
    t['e']['a'] = 'hello'
    eq_(t.embed.attr, 'hello')


def test_instance_embed_embed_attr():
    t = EmbedTestDoc()
    t['e'] = {}
    t['e']['e'] = {}
    t['e']['e']['a'] = 'hello'
    eq_(t.embed.embed.attr, 'hello')


def test_instance_replace_attr():
    t = EmbedTestDoc()
    t['a'] = 'hello'
    t.attr = 'goodbye'
    eq_(t['a'], 'goodbye')
    eq_(t.attr, 'goodbye')


def test_instance_replace_embed_attr():
    t = EmbedTestDoc()
    t['e'] = {}
    t['e']['a'] = 'hello'
    t.embed.attr = 'goodbye'
    eq_(t['e']['a'], 'goodbye')
    eq_(t.embed.attr, 'goodbye')


def test_instance_replace_embed_embed_attr():
    t = EmbedTestDoc()
    t['e'] = {}
    t['e']['e'] = {}
    t['e']['e']['a'] = 'hello'
    t.embed.embed.attr = 'goodbye'
    eq_(t['e']['e']['a'], 'goodbye')
    eq_(t.embed.embed.attr, 'goodbye')


def test_instance_set_attr():
    t = EmbedTestDoc()
    t.attr = 'hello'
    eq_(t['a'], 'hello')
    eq_(t.attr, 'hello')


def test_instance_set_embed_attr():
    t = EmbedTestDoc()
    t.embed.attr = 'hello'
    eq_(t['e']['a'], 'hello')
    eq_(t.embed.attr, 'hello')


def test_instance_set_embed_embed_attr():
    t = EmbedTestDoc()
    t.embed.embed.attr = 'hello'
    eq_(t['e']['e']['a'], 'hello')
    eq_(t.embed.embed.attr, 'hello')


def test_instance_set_embed_embed_attr2():
    t = EmbedTestDoc()
    t.embed.embed.attr = 'hello'
    eq_(t, {'e': {'e': {'a': 'hello'}}})


def test_instance_set_embed_embed_attr_side_effects():
    t = EmbedTestDoc()
    t.embed.embed.attr = 'hello'
    t.embed.embed.attr
    eq_(t['e']['e']['a'], 'hello')
    eq_(t.embed.embed.attr, 'hello')


def test_instance_embed_override():
    t = EmbedTestDoc()
    t.embed = 'hello'
    eq_(t, {'e': 'hello'})


def test_instance_embed_embed_override():
    t = EmbedTestDoc()
    t.embed.embed = 'hello'
    eq_(t, {'e': {'e': 'hello'}})


def test_delete_attr():
    t = EmbedTestDoc()
    t.attr = 'hello'
    eq_(t, {'a': 'hello'})
    del t.attr
    eq_(t, {})


def test_delete_embed_attr():
    t = EmbedTestDoc()
    t.embed.attr = 'hello'
    eq_(t, {'e': {'a': 'hello'}})
    del t.embed.attr
    eq_(t, {})


def test_delete_embed_embed_attr():
    t = EmbedTestDoc()
    t.embed.embed.attr = 'hello'
    eq_(t, {'e': {'e': {'a': 'hello'}}})
    del t.embed.embed.attr
    eq_(t, {})


def test_delete_partial_key():
    t = EmbedTestDoc()
    t.embed.embed.attr = 'hello'
    t['e']['e']['b'] = 'world'
    eq_(t, {'e': {'e': {'a': 'hello', 'b': 'world'}}})
    del t.embed.embed.attr
    eq_(t, {'e': {'e': {'b': 'world'}}})


def test_delete_subdoc():
    t = EmbedTestDoc()
    t.embed.embed.attr = 'hello'
    t['e']['e']['b'] = 'world'
    eq_(t, {'e': {'e': {'a': 'hello', 'b': 'world'}}})
    del t.embed
    eq_(t, {})


def test_delete_subsubdoc():
    t = EmbedTestDoc()
    t.embed.embed.attr = 'hello'
    t['e']['e']['b'] = 'world'
    eq_(t, {'e': {'e': {'a': 'hello', 'b': 'world'}}})
    del t.embed.embed
    eq_(t, {})


def test_embed_asdict():
    t = EmbedTestDoc()
    t.embed.embed.attr = 'hello'
    eq_(t._asdict(), {'embed': {'embed': {'attr': 'hello'}}})


def test_embed_retrieval_types():
    class Retriever(EmbedTestDoc):
        config_database = DB_NAME
        config_collection = 'test'

    t = Retriever()
    t.embed.embed.attr = 'hello'
    with _TestDB:
        doc_id = Retriever.insert(t)
        doc = Retriever.find_one({Retriever._id: doc_id})

    eq_(doc, {'_id': doc_id, 'e': {'e': {'a': 'hello'}}})
    eq_(type(doc), Retriever)
    eq_(type(doc['e']), dict)
    eq_(type(doc['e']['e']), dict)
    eq_(type(doc['e']['e']['a']), unicode)


def test_always_id():
    class TestId(Document):
        pass

    eq_(TestId._id, '_id')


def test_always_id_subclass():
    class TestId(Document):
        pass

    class TestSub(TestId):
        pass

    eq_(TestSub._id, '_id')


def test_find_returns_same_class():
    doc = _TestDoc()
    doc.user_name = 'testing find'

    with _TestDB:
        _TestDoc.insert(doc)

    ok_(doc._id)

    with _TestDB:
        doc = list(_TestDoc.find({_TestDoc._id: doc._id}))

    ok_(doc)
    doc = doc[0]
    eq_(type(doc), _TestDoc)


def test_find_one_returns_same_class():
    doc = _TestDoc()
    doc.user_name = 'testing find_one'

    with _TestDB:
        _TestDoc.insert(doc)

    ok_(doc._id)

    with _TestDB:
        doc = _TestDoc.find_one({_TestDoc._id: doc._id})

    ok_(doc)
    eq_(doc.user_name, 'testing find_one')
    eq_(type(doc), _TestDoc)


def test_find_and_modify_returns_same_class():
    doc = _TestDoc()
    doc.user_name = 'testing find_and_modify'

    with _TestDB:
        _TestDoc.insert(doc)

    ok_(doc._id)

    with _TestDB:
        doc = _TestDoc.find_and_modify({_TestDoc._id: doc._id},
                {'$set': {_TestDoc.user_name: 'tested find_and_modify'}},
                new=True)

    ok_(doc)
    eq_(doc.user_name, 'tested find_and_modify')
    eq_(type(doc), _TestDoc)


def test_mapped_keys():
    class TestMapped(Document):
        key1 = '1'
        key2 = '2'
        key3 = '3'

    eq_(sorted(TestMapped.mapped_keys()), ['1', '2', '3'])


def test_mapped_attributes():
    class TestMapped(Document):
        key1 = '1'
        key2 = '2'
        key3 = '3'

    eq_(sorted(TestMapped.mapped_attributes()), ['key1', 'key2', 'key3'])


def test_embed_mapped_keys():
    class TestMapped(Document):
        key1 = '1'
        key2 = '2'
        key3 = '3'

        embed = Embed('e')

    eq_(sorted(TestMapped.mapped_keys()), ['1', '2', '3', 'e'])


def test_embed_mapped_attributes():
    class TestMapped(Document):
        key1 = '1'
        key2 = '2'
        key3 = '3'

        embed = Embed('e')

    eq_(sorted(TestMapped.mapped_attributes()),
            ['embed', 'key1', 'key2', 'key3'])


def test_find_and_modify_doesnt_error_when_none():
    with _TestDB:
        doc = _TestDoc.find_and_modify({_TestDoc._id: 'doesnt_exist'},
                {'$set': {'foo': 1}})

    eq_(doc, None)


