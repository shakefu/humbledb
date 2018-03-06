import six
import mock
import pytool
import pyconfig
from six.moves import xrange

import humbledb
from humbledb import Mongo, Document, Embed, _version
from ..util import eq_, ok_, raises, DBTest, database_name


# The safe= keyword doesn't exist in 3.0
if _version._lt('3.0.0'):
    _safe = {'safe': True}
else:
    _safe = {}


def teardown():
    DBTest.connection.drop_database(database_name())


def cache_for(val):
    # This is a work around for the version changing the cache argument
    if _version._lt('2.3'):
        return {'ttl': val}
    return {'cache_for': val}


class DocTest(Document):
    config_database = database_name()
    config_collection = 'test'

    user_name = 'u'


class EmbedTestDoc(Document):
    attr = 'a'
    attr2 = 'a2'

    embed = Embed('e')
    embed.attr = 'a'

    embed.embed = Embed('e')
    embed.embed.attr = 'a'


def test_delete():
    n = DocTest()
    n.user_name = 'test'
    ok_(DocTest.user_name in n)
    del n.user_name
    eq_(DocTest.user_name in n, False)


@raises(RuntimeError)
def test_without_context():
    DocTest.find_one()


@raises(TypeError)
def test_bad_name():
    class Test(Document):
        items = 'i'


@raises(RuntimeError)
def test_missing_database():
    class Test(Document):
        config_collection = 'test'

    with DBTest:
        Test.collection


@raises(RuntimeError)
def test_missing_collection():
    class Test(Document):
        config_database = database_name()

    with DBTest:
        Test.collection


@raises(AttributeError)
def test_bad_attribute():
    with DBTest:
        DocTest.foo


def test_ignore_method():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'

        def test(self):
            pass

    ok_(callable(Test.test))


def test_unmapped_fields():
    n = DocTest(foo='bar')
    ok_('foo' in n)
    eq_(n['foo'], 'bar')
    ok_('foo' in n.for_json())
    eq_(n.for_json()['foo'], 'bar')


def test_instance_dictproxy_attr():
    _doc = DocTest()
    _doc.user_name = 'value'
    eq_(_doc.user_name, 'value')
    eq_(DocTest().user_name, {})


def test_ensure_indexes_called():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'
        config_indexes = ['user_name']

        user_name = 'u'

    with DBTest:
        with mock.patch.object(Test, '_ensure_indexes') as _ensure:
            eq_(Test._ensure_indexes, _ensure)
            Test._ensured = None
            Test.find_one()
            _ensure.assert_called_once()


def test_ensure_indexes_calls_ensure_index():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'
        config_indexes = ['user_name']

        user_name = 'u'

    with DBTest:
        with mock.patch.object(Test, 'collection') as coll:
            coll.find_one.__name__ = 'find_one'
            Test._ensured = None
            Test.find_one()
            coll.ensure_index.assert_called_with(
                    Test.user_name,
                    background=True,
                    **cache_for(60*60*24))


def test_ensure_indexes_reload_hook():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'
        config_indexes = ['user_name']

        user_name = 'u'

    with DBTest:
        Test.find_one()

    eq_(Test._ensured, True)
    pyconfig.reload()
    eq_(Test._ensured, False)


def test_wrap_methods():
    with DBTest:
        with mock.patch.object(DocTest, '_wrap') as _wrap:
            _wrap.return_value = '_wrapper'
            eq_(DocTest.find, _wrap.return_value)
            _wrap.assert_called_once()


def test_wrap_method_behaves_itself():
    with DBTest:
        with mock.patch.object(DocTest, 'collection') as coll:
            coll.find.__name__ = 'find'
            coll.find.return_value = mock.Mock(spec=humbledb.cursor.Cursor)
            DocTest.find()
            coll.find.assert_called_with()


def test_update_wrapping():
    with DBTest:
        eq_(DocTest._wrap_update, DocTest.update)


def test_document_repr():
    # Coverage all the coverage!
    d = {'foo': 'bar'}
    eq_(repr(DocTest(d)), "DocTest({})".format(repr(d)))


def test_for_json():
    eq_(DocTest({'u': 'test_name'}).for_json(), {'user_name': 'test_name'})


def test_for_json_list():
    eq_(DocTest({'u': ["foo", ["bar"]]}).for_json(), {'user_name': ["foo",
        ["bar"]]})


def test_for_json_embedded_list():
    eq_(EmbedTestDoc({'e': [{'e': [{'a': 1}]}]}).for_json(), {'embed':
        [{'embed': [{'attr': 1}]}]})


def test_non_mapped_attribute_assignment_works_fine():
    d = DocTest()
    d.foo = "bar"
    eq_(d.foo, "bar")


@raises(AttributeError)
def test_non_mapped_attribute_deletion_works():
    d = DocTest()
    d.foo = "bar"
    eq_(d.foo, "bar")
    del d.foo
    d.foo


def test_nonstring():
    _instance = object()

    class _TestNonString(Document):
        config_database = database_name()
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
    eq_(_TestNonString().ok, {})


def test_property_attribute():
    class _TestProperty(Document):
        config_database = database_name()
        config_collection = 'test'

        @property
        def attr(self):
            return self

        foo = 'bar'

    eq_(_TestProperty._name_map.filtered(), {'foo': 'bar'})
    tp = _TestProperty()
    eq_(tp.attr, tp)


def test_inheritance():
    class DocTest2(DocTest):
        pass

    eq_(DocTest2.user_name, DocTest.user_name)
    eq_(DocTest2.config_database, DocTest.config_database)
    eq_(DocTest2.config_collection, DocTest.config_collection)

    # This is to ensure the collection is accessible, e.g. not raising an error
    with DBTest:
        DocTest2.collection


def test_inheritance_combined():
    class DocTest2(DocTest):
        new_name = 'n'

    eq_(DocTest2.new_name, 'n')
    eq_(DocTest2.user_name, DocTest.user_name)


def test_classproperty_attribute():
    class _TestClassProp(Document):
        config_database = database_name()
        config_collection = 'test'

        @pytool.lang.classproperty
        def attr(cls):
            return cls

    eq_(_TestClassProp.attr, _TestClassProp)
    eq_(_TestClassProp().attr, _TestClassProp)


def test_self_insertion():
    t = DocTest()
    with DBTest:
        type(t).insert(t)

    ok_(t._id)


def test_cls_self_insertion():
    with DBTest:
        DocTest.insert({'_id': 'tsci', 't': True})
        ok_(DocTest.find_one({'_id': 'tsci'}))


@raises(AttributeError)
def test_collection_attributes_not_accessible_from_instance():
    t = DocTest()
    with DBTest:
        t.find


def test_collection_accessible_from_instance():
    t = DocTest()
    with DBTest:
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


def test_embed_for_json():
    t = EmbedTestDoc()
    t.embed.embed.attr = 'hello'
    eq_(t.for_json(), {'embed': {'embed': {'attr': 'hello'}}})


def test_embed_retrieval_types():
    class Retriever(EmbedTestDoc):
        config_database = database_name()
        config_collection = 'test'

    t = Retriever()
    t.embed.embed.attr = 'hello'
    with DBTest:
        doc_id = Retriever.insert(t)
        doc = Retriever.find_one({Retriever._id: doc_id})

    eq_(doc, {'_id': doc_id, 'e': {'e': {'a': 'hello'}}})
    eq_(type(doc), Retriever)
    eq_(type(doc['e']), dict)
    eq_(type(doc['e']['e']), dict)
    eq_(type(doc['e']['e']['a']), six.text_type)


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
    doc = DocTest()
    doc.user_name = 'testing find'

    with DBTest:
        DocTest.insert(doc)

    ok_(doc._id)

    with DBTest:
        doc = list(DocTest.find({DocTest._id: doc._id}))

    ok_(doc)
    doc = doc[0]
    eq_(type(doc), DocTest)


def test_find_one_returns_same_class():
    doc = DocTest()
    doc.user_name = 'testing find_one'

    with DBTest:
        DocTest.insert(doc)

    ok_(doc._id)

    with DBTest:
        doc = DocTest.find_one({DocTest._id: doc._id})

    ok_(doc)
    eq_(doc.user_name, 'testing find_one')
    eq_(type(doc), DocTest)


def test_find_and_modify_returns_same_class():
    doc = DocTest()
    doc.user_name = 'testing find_and_modify'

    with DBTest:
        DocTest.insert(doc)

    ok_(doc._id)

    with DBTest:
        doc = DocTest.find_and_modify({DocTest._id: doc._id},
                {'$set': {DocTest.user_name: 'tested find_and_modify'}},
                new=True)

    ok_(doc)
    eq_(doc.user_name, 'tested find_and_modify')
    eq_(type(doc), DocTest)


def test_find_and_modify_doesnt_error_when_none():
    with DBTest:
        doc = DocTest.find_and_modify({DocTest._id: 'doesnt_exist'},
                {'$set': {'foo': 1}})

    eq_(doc, None)


def test_list_subdocuments_should_be_regular_dicts():
    class ListTest(DocTest):
        vals = 'v'
    # Create a new instance
    l = ListTest()
    vals = [{'a': {'test': True}, 'b': 2}]
    # Insert the instance
    with Mongo:
        l_id = ListTest.insert(l)
        # Set the list
        ListTest.update({ListTest._id: l_id}, {'$set': {ListTest.vals: vals}})
        # Re-retrieve the instance to allow pymongo to coerce types
        l = list(ListTest.find({ListTest._id: l_id}))[0]
        l2 = ListTest.find_one({ListTest._id: l_id})
    # Check the type
    ok_(not isinstance(l.vals[0], Document), l.vals[0])
    ok_(not isinstance(l2.vals[0], Document), l2.vals[0])


def test_unpatching_document_update_works_nicely():
    with DBTest:
        original_update = DocTest.update
        with mock.patch.object(DocTest, 'update') as update:
            update.return_value = 'updated'
            value = DocTest.update({DocTest._id: 1}, {'$set':
                {DocTest.user_name: 'hello'}})
            eq_(value, 'updated')
        eq_(DocTest.update, original_update)


def test_unmapped_subdocument_saves_and_retrieves_ok():
    class Test(DocTest):
        val = 'v'

    t = Test()
    eq_(t.val, {})
    t.val['hello'] = 'world'

    with DBTest:
        t_id = Test.insert(t)
        t = Test.find_one({Test._id: t_id})

    eq_(t.val, {'hello': 'world'})


@raises(AttributeError)
def test_name_attribute():
    class Test(Document):
        pass

    Test.name


@raises(TypeError)
def test_config_indexes_must_be_a_list():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'
        config_indexes = 'foo'


def test_exercise_normal_index():
    class Test(Document):
        config_database = database_name()
        config_collection = 'potato'
        config_indexes = ['user_name']

        user_name = 'u'

    with DBTest:
        Test.find_one()


def test_callable_default_creates_saved_defaults():
    func = lambda: 1
    class Default(DocTest):
        saved = 's', func

    t = Default()
    eq_(t._saved_defaults, {'s': func})


def test_saved_default_is_returned_on_instance():
    func = lambda: 1
    class Default(DocTest):
        saved = 's', func

    t = Default()
    eq_(t.saved, 1)


def test_saved_default_is_part_of_the_doc_after_access():
    func = lambda: 1
    class Default(DocTest):
        saved = 's', func

    t = Default()
    eq_(t.saved, 1)
    eq_(t, {Default.saved: 1})


def test_saved_default_memoizes_first_value_on_multiple_accesses():
    s = [0]
    def func():
        s[0] += 1
        return s[0]

    class Default(DocTest):
        saved = 's', func

    t = Default()
    eq_(t.saved, 1)
    eq_(t.saved, 1)
    eq_(s[0], 1)


def test_saved_default_is_inheritable():
    class Default(DocTest):
        saved = 's', lambda: 1

    class Sub(Default):
        other = 'o', lambda: 2

    class Over(Default):
        saved = 's', lambda: 3

    d = Default()
    eq_(d.saved, 1)

    d = Sub()
    eq_(d.saved, 1)
    eq_(d.other, 2)

    d = Over()
    eq_(d.saved, 3)


def test_default_is_inheritable():
    class Default(DocTest):
        val = 's', 1

    class Sub(Default):
        other = 'o', 2

    class Over(Default):
        val = 's', 3

    d = Default()
    eq_(d.val, 1)

    d = Sub()
    eq_(d.val, 1)
    eq_(d.other, 2)

    d = Over()
    eq_(d.val, 3)


def test_saved_default_is_set_on_saving():
    class Default(DocTest):
        saved = 's', lambda: 1

    d = Default()
    with DBTest:
        _id = Default.save(d, **_safe)
        d = Default.find_one(_id)

    d.pop('_id')
    eq_(dict(d), {Default.saved: 1})



def test_saved_default_is_set_on_inserting():
    class Default(DocTest):
        saved = 's', lambda: 1

    d = Default()
    with DBTest:
        _id = Default.insert(d, **_safe)
        d = Default.find_one(_id)

    d.pop('_id')
    eq_(dict(d), {Default.saved: 1})


def test_saved_default_is_set_on_multiple_inserts():
    class Default(DocTest):
        saved = 's', lambda: 1

    docs = []
    for i in xrange(3):
        d = Default()
        d._id = 'test_saved_default_%s' % i
        docs.append(d)

    with DBTest:
        _ids = Default.insert(docs, **_safe)
        eq_(len(_ids), 3)
        docs = list(Default.find({Default._id: {'$in': _ids}}))

    eq_(len(docs), 3)
    for doc in docs:
        doc.pop('_id')
        eq_(dict(doc), {Default.saved: 1})


def test_saved_defaults_are_set_in_json():
    class Default(DocTest):
        saved = 's', lambda: 1

    d = Default()
    eq_(d.for_json(), {'saved': 1})


def test_defaults_are_set_in_json_but_not_in_doc():
    class Default(DocTest):
        val = 'v', 1

    d = Default()
    eq_(d.for_json(), {'val': 1})
    eq_(d.get(Default.val, None), None)


def test_saved_defaults_with_defaults_as_json():
    class Default(DocTest):
        saved = 's', lambda: 1
        val = 'v', 2

    d = Default()
    eq_(d.for_json(), {'val': 2, 'saved': 1})
    eq_(d.get(Default.val, None), None)
    eq_(d.saved, 1)


@raises(AttributeError)
def test_embedded_defaults_are_unmapped():
    class Embedded(DocTest):
        val = Embed('v')
        val.sub = 's', 1
        val.sub2 = 's'

    eq_(Embedded.val.sub, ('s', 1))
    eq_(Embedded.val.sub2, 'v.s')
    d = Embedded()
    d.val.sub  # This will raise AttributeError since val.sub is unmapped


def test_only_two_tuples_with_leading_string_are_interpreted_as_defaults():
    v1 = ('a',)
    v2 = ('b', 2)
    v3 = ('c', 3, 4)
    v4 = (1, 2)

    class TupleTest(DocTest):
        attr1 = v1
        attr2 = v2
        attr3 = v3
        attr4 = v4

    eq_(TupleTest.attr1, v1)
    eq_(TupleTest.attr2, 'b')
    eq_(TupleTest.attr3, v3)
    eq_(TupleTest.attr4, v4)
    d = TupleTest()
    eq_(d.attr1, v1)
    eq_(d.attr2, 2)
    eq_(d.attr3, v3)
    eq_(d.attr4, v4)


def test_update_with_safe_keyword_doesnt_break_pymongo_3():
    with DBTest:
        DocTest.update({'_id': 'update_safe_pymongo_3'}, {'$set': {'ok':
            True}}, upsert=True, safe=True)


def test_save_with_safe_keyword_doesnt_break_pymongo_3():
    with DBTest:
        DocTest.save({'_id': 'save_safe_pymongo_3'}, safe=True)


def test_insert_with_safe_keyword_doesnt_break_pymongo_3():
    with DBTest:
        DocTest.insert({'_id': 'insert_safe_pymongo_3'}, safe=True)

