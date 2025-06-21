import mock
import pyconfig
import pytest
import pytool

import humbledb
from humbledb import Document, Embed, Mongo, _version

from ..util import DBTest, database_name

# The safe= keyword doesn't exist in 3.0
if _version._lt("3.0.0"):
    _safe = {"safe": True}
else:
    _safe = {}


def teardown():
    DBTest.connection.drop_database(database_name())


def cache_for(val):
    # This is a work around for the version changing the cache argument
    if _version._lt("2.3"):
        return {"ttl": val}
    return {"cache_for": val}


class DocTest(Document):
    config_database = database_name()
    config_collection = "test"

    user_name = "u"


class EmbedTestDoc(Document):
    attr = "a"
    attr2 = "a2"

    embed = Embed("e")
    embed.attr = "a"

    embed.embed = Embed("e")
    embed.embed.attr = "a"


def test_delete():
    n = DocTest()
    n.user_name = "test"
    assert DocTest.user_name in n
    del n.user_name
    assert DocTest.user_name not in n


def test_without_context():
    with pytest.raises(RuntimeError):
        DocTest.find_one()


def test_bad_name():
    with pytest.raises(TypeError):

        class Test(Document):
            items = "i"


def test_missing_database():
    with pytest.raises(RuntimeError):

        class Test(Document):
            config_collection = "test"

        with DBTest:
            Test.collection


def test_missing_collection():
    with pytest.raises(RuntimeError):

        class Test(Document):
            config_database = database_name()

        with DBTest:
            Test.collection


def test_bad_attribute():
    with pytest.raises(AttributeError):
        with DBTest:
            DocTest.foo


def test_ignore_method():
    class Test(Document):
        config_database = database_name()
        config_collection = "test"

        def test(self):
            pass

    assert callable(Test.test)


def test_unmapped_fields():
    n = DocTest(foo="bar")
    assert "foo" in n
    assert n["foo"] == "bar"
    assert "foo" in n.for_json()
    assert n.for_json()["foo"] == "bar"


def test_instance_dictproxy_attr():
    _doc = DocTest()
    _doc.user_name = "value"
    assert _doc.user_name == "value"
    assert DocTest().user_name == {}


def test_ensure_indexes_called():
    if _version._gte("4.0"):
        pytest.skip("ensure_index was removed in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = ["user_name"]

        user_name = "u"

    with DBTest:
        with mock.patch.object(Test, "_ensure_indexes") as _ensure:
            assert Test._ensure_indexes == _ensure
            Test._ensured = None
            Test.find_one()
            _ensure.assert_called_once()


def test_ensure_indexes_calls_ensure_index_pymongo_4():
    if _version._lt("4.0"):
        pytest.skip("create_index was introduced in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = ["user_name"]

        user_name = "u"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.create_index.assert_called_with(Test.user_name, background=True)


def test_ensure_indexes_calls_ensure_index():
    if _version._gte("4.0"):
        pytest.skip("ensure_index was removed in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = ["user_name"]

        user_name = "u"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.ensure_index.assert_called_with(
                Test.user_name, background=True, **cache_for(60 * 60 * 24)
            )


def test_ensure_indexes_calls_create_index_pymongo_4():
    if _version._lt("4.0"):
        pytest.skip("create_index was introduced in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = ["user_name"]

        user_name = "u"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.create_index.assert_called_with(Test.user_name, background=True)


def test_ensure_indexes_reload_hook():
    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = ["user_name"]

        user_name = "u"

    with DBTest:
        Test.find_one()

    assert Test._ensured is True
    pyconfig.reload()
    assert Test._ensured is False


def test_wrap_methods():
    with DBTest:
        with mock.patch.object(DocTest, "_wrap") as _wrap:
            _wrap.return_value = "_wrapper"
            assert DocTest.find == _wrap.return_value
            _wrap.assert_called_once()


def test_wrap_method_behaves_itself():
    with DBTest:
        with mock.patch.object(DocTest, "collection") as coll:
            coll.find.__name__ = "find"
            coll.find.return_value = mock.Mock(spec=humbledb.cursor.Cursor)
            DocTest.find()
            coll.find.assert_called_with()


def test_update_wrapping():
    with DBTest:
        assert DocTest._wrap_update == DocTest.update


def test_document_repr():
    # Coverage all the coverage!
    d = {"foo": "bar"}
    assert repr(DocTest(d)) == "DocTest({})".format(repr(d))


def test_for_json():
    assert DocTest({"u": "test_name"}).for_json() == {"user_name": "test_name"}


def test_for_json_list():
    assert DocTest({"u": ["foo", ["bar"]]}).for_json() == {
        "user_name": ["foo", ["bar"]]
    }


def test_for_json_embedded_list():
    assert EmbedTestDoc({"e": [{"e": [{"a": 1}]}]}).for_json() == {
        "embed": [{"embed": [{"attr": 1}]}]
    }


def test_non_mapped_attribute_assignment_works_fine():
    d = DocTest()
    d.foo = "bar"
    assert d.foo == "bar"


def test_non_mapped_attribute_deletion_works():
    d = DocTest()
    d.foo = "bar"
    assert d.foo == "bar"
    del d.foo
    with pytest.raises(AttributeError):
        d.foo


def test_nonstring():
    _instance = object()

    class _TestNonString(Document):
        config_database = database_name()
        config_collection = "test"

        foo = 2
        bar = True
        cls = object
        instance = _instance
        ok = "OK"

    assert _TestNonString._name_map.filtered() == {"ok": "OK"}
    assert _TestNonString.foo == 2
    assert _TestNonString.bar is True
    assert _TestNonString.cls is object
    assert _TestNonString.instance is _instance
    assert _TestNonString.ok == "OK"
    assert _TestNonString().foo == 2
    assert _TestNonString().bar is True
    assert _TestNonString().cls is object
    assert _TestNonString().instance is _instance
    assert _TestNonString().ok == {}


def test_property_attribute():
    class _TestProperty(Document):
        config_database = database_name()
        config_collection = "test"

        @property
        def attr(self):
            return self

        foo = "bar"

    assert _TestProperty._name_map.filtered() == {"foo": "bar"}
    tp = _TestProperty()
    assert tp.attr is tp


def test_inheritance():
    class DocTest2(DocTest):
        pass

    assert DocTest2.user_name == DocTest.user_name
    assert DocTest2.config_database == DocTest.config_database
    assert DocTest2.config_collection == DocTest.config_collection

    # This is to ensure the collection is accessible, e.g. not raising an error
    with DBTest:
        DocTest2.collection


def test_inheritance_combined():
    class DocTest2(DocTest):
        new_name = "n"

    assert DocTest2.new_name == "n"
    assert DocTest2.user_name == DocTest.user_name


def test_classproperty_attribute():
    class _TestClassProp(Document):
        config_database = database_name()
        config_collection = "test"

        @pytool.lang.classproperty
        def attr(cls):
            return cls

    assert _TestClassProp.attr is _TestClassProp
    assert _TestClassProp().attr is _TestClassProp


def test_self_insertion():
    t = DocTest()
    with DBTest:
        type(t).insert(t)

    assert t._id


def test_cls_self_insertion():
    with DBTest:
        DocTest.insert({"_id": "tsci", "t": True})
        assert DocTest.find_one({"_id": "tsci"})


def test_collection_attributes_not_accessible_from_instance():
    t = DocTest()
    with pytest.raises(AttributeError):
        with DBTest:
            t.find


def test_collection_accessible_from_instance():
    t = DocTest()
    with DBTest:
        t.collection


def test_attr():
    assert EmbedTestDoc.attr == "a"


def test_embed():
    assert EmbedTestDoc.embed == "e"


def test_embed_attr():
    assert EmbedTestDoc.embed.attr == "e.a"


def test_embed_embed():
    assert EmbedTestDoc.embed.embed == "e.e"


def test_embed_embed_attr():
    assert EmbedTestDoc.embed.embed.attr == "e.e.a"


def test_instance_attr():
    t = EmbedTestDoc()
    t["a"] = "hello"
    assert t.attr == "hello"


def test_instance_embed_attr():
    t = EmbedTestDoc()
    t["e"] = {}
    t["e"]["a"] = "hello"
    assert t.embed.attr == "hello"


def test_instance_embed_embed_attr():
    t = EmbedTestDoc()
    t["e"] = {}
    t["e"]["e"] = {}
    t["e"]["e"]["a"] = "hello"
    assert t.embed.embed.attr == "hello"


def test_instance_replace_attr():
    t = EmbedTestDoc()
    t["a"] = "hello"
    t.attr = "goodbye"
    assert t["a"] == "goodbye"
    assert t.attr == "goodbye"


def test_instance_replace_embed_attr():
    t = EmbedTestDoc()
    t["e"] = {}
    t["e"]["a"] = "hello"
    t.embed.attr = "goodbye"
    assert t["e"]["a"] == "goodbye"
    assert t.embed.attr == "goodbye"


def test_instance_replace_embed_embed_attr():
    t = EmbedTestDoc()
    t["e"] = {}
    t["e"]["e"] = {}
    t["e"]["e"]["a"] = "hello"
    t.embed.embed.attr = "goodbye"
    assert t["e"]["e"]["a"] == "goodbye"
    assert t.embed.embed.attr == "goodbye"


def test_instance_set_attr():
    t = EmbedTestDoc()
    t.attr = "hello"
    assert t["a"] == "hello"
    assert t.attr == "hello"


def test_instance_set_embed_attr():
    t = EmbedTestDoc()
    t.embed.attr = "hello"
    assert t["e"]["a"] == "hello"
    assert t.embed.attr == "hello"


def test_instance_set_embed_embed_attr():
    t = EmbedTestDoc()
    t.embed.embed.attr = "hello"
    assert t["e"]["e"]["a"] == "hello"
    assert t.embed.embed.attr == "hello"


def test_instance_set_embed_embed_attr2():
    t = EmbedTestDoc()
    t.embed.embed.attr = "hello"
    assert t == {"e": {"e": {"a": "hello"}}}


def test_instance_set_embed_embed_attr_side_effects():
    t = EmbedTestDoc()
    t.embed.embed.attr = "hello"
    t.embed.embed.attr
    assert t["e"]["e"]["a"] == "hello"
    assert t.embed.embed.attr == "hello"


def test_instance_embed_override():
    t = EmbedTestDoc()
    t.embed = "hello"
    assert t == {"e": "hello"}


def test_instance_embed_embed_override():
    t = EmbedTestDoc()
    t.embed.embed = "hello"
    assert t == {"e": {"e": "hello"}}


def test_delete_attr():
    t = EmbedTestDoc()
    t.attr = "hello"
    assert t == {"a": "hello"}
    del t.attr
    assert t == {}


def test_delete_embed_attr():
    t = EmbedTestDoc()
    t.embed.attr = "hello"
    assert t == {"e": {"a": "hello"}}
    del t.embed.attr
    assert t == {}


def test_delete_embed_embed_attr():
    t = EmbedTestDoc()
    t.embed.embed.attr = "hello"
    assert t == {"e": {"e": {"a": "hello"}}}
    del t.embed.embed.attr
    assert t == {}


def test_delete_partial_key():
    t = EmbedTestDoc()
    t.embed.embed.attr = "hello"
    t["e"]["e"]["b"] = "world"
    assert t == {"e": {"e": {"a": "hello", "b": "world"}}}
    del t.embed.embed.attr
    assert t == {"e": {"e": {"b": "world"}}}


def test_delete_subdoc():
    t = EmbedTestDoc()
    t.embed.embed.attr = "hello"
    t["e"]["e"]["b"] = "world"
    assert t == {"e": {"e": {"a": "hello", "b": "world"}}}
    del t.embed
    assert t == {}


def test_delete_subsubdoc():
    t = EmbedTestDoc()
    t.embed.embed.attr = "hello"
    t["e"]["e"]["b"] = "world"
    assert t == {"e": {"e": {"a": "hello", "b": "world"}}}
    del t.embed.embed
    assert t == {}


def test_embed_for_json():
    t = EmbedTestDoc()
    t.embed.embed.attr = "hello"
    assert t.for_json() == {"embed": {"embed": {"attr": "hello"}}}


def test_embed_retrieval_types():
    class Retriever(EmbedTestDoc):
        config_database = database_name()
        config_collection = "test"

    t = Retriever()
    t.embed.embed.attr = "hello"
    with DBTest:
        doc_id = Retriever.insert(t)
        doc = Retriever.find_one({Retriever._id: doc_id})

    assert doc == {"_id": doc_id, "e": {"e": {"a": "hello"}}}
    assert type(doc) is Retriever
    assert type(doc["e"]) is dict
    assert type(doc["e"]["e"]) is dict
    assert type(doc["e"]["e"]["a"]) is str


def test_always_id():
    class TestId(Document):
        pass

    assert TestId._id == "_id"


def test_always_id_subclass():
    class TestId(Document):
        pass

    class TestSub(TestId):
        pass

    assert TestSub._id == "_id"


def test_find_returns_same_class():
    doc = DocTest()
    doc.user_name = "testing find"

    with DBTest:
        DocTest.insert(doc)

    assert doc._id

    with DBTest:
        doc = list(DocTest.find({DocTest._id: doc._id}))

    assert doc
    doc = doc[0]
    assert type(doc) is DocTest


def test_find_one_returns_same_class():
    doc = DocTest()
    doc.user_name = "testing find_one"

    with DBTest:
        DocTest.insert(doc)

    assert doc._id

    with DBTest:
        doc = DocTest.find_one({DocTest._id: doc._id})

    assert doc
    assert doc.user_name == "testing find_one"
    assert type(doc) is DocTest


def test_find_and_modify_returns_same_class():
    doc = DocTest()
    doc.user_name = "testing find_and_modify"

    with DBTest:
        DocTest.insert(doc)

    assert doc._id

    with DBTest:
        doc = DocTest.find_and_modify(
            {DocTest._id: doc._id},
            {"$set": {DocTest.user_name: "tested find_and_modify"}},
            new=True,
        )

    assert doc
    assert doc.user_name == "tested find_and_modify"
    assert type(doc) is DocTest


def test_find_and_modify_doesnt_error_when_none():
    with DBTest:
        doc = DocTest.find_and_modify(
            {DocTest._id: "doesnt_exist"}, {"$set": {"foo": 1}}
        )

    assert doc is None


def test_list_subdocuments_should_be_regular_dicts():
    pytest.skip("This test is slow, need to fix it later")

    class ListTest(DocTest):
        vals = "v"

    # Create a new instance
    items = ListTest()
    vals = [{"a": {"test": True}, "b": 2}]
    # Insert the instance
    with Mongo:
        l_id = ListTest.insert(items)
        # Set the list
        ListTest.update({ListTest._id: l_id}, {"$set": {ListTest.vals: vals}})
        # Re-retrieve the instance to allow pymongo to coerce types
        items = list(ListTest.find({ListTest._id: l_id}))[0]
        l2 = ListTest.find_one({ListTest._id: l_id})
    # Check the type
    assert not isinstance(items.vals[0], Document)
    assert not isinstance(l2.vals[0], Document)


def test_unpatching_document_update_works_nicely():
    with DBTest:
        original_update = DocTest.update
        with mock.patch.object(DocTest, "update") as update:
            update.return_value = "updated"
            value = DocTest.update(
                {DocTest._id: 1}, {"$set": {DocTest.user_name: "hello"}}
            )
            assert value == "updated"
        assert DocTest.update == original_update


def test_unmapped_subdocument_saves_and_retrieves_ok():
    class Test(DocTest):
        val = "v"

    t = Test()
    assert t.val == {}
    t.val["hello"] = "world"

    with DBTest:
        t_id = Test.insert(t)
        t = Test.find_one({Test._id: t_id})

    assert t.val == {"hello": "world"}


def test_name_attribute():
    with pytest.raises(AttributeError):

        class Test(Document):
            pass

        Test.name


def test_config_indexes_must_be_a_list():
    with pytest.raises(TypeError):

        class Test(Document):
            config_database = database_name()
            config_collection = "test"
            config_indexes = "foo"


def test_exercise_normal_index():
    class Test(Document):
        config_database = database_name()
        config_collection = "potato"
        config_indexes = ["user_name"]

        user_name = "u"

    with DBTest:
        Test.find_one()


def test_callable_default_creates_saved_defaults():
    def func():
        return 1

    class Default(DocTest):
        saved = "s", func

    t = Default()
    assert t._saved_defaults == {"s": func}


def test_saved_default_is_returned_on_instance():
    def func():
        return 1

    class Default(DocTest):
        saved = "s", func

    t = Default()
    assert t.saved == 1


def test_saved_default_is_part_of_the_doc_after_access():
    def func():
        return 1

    class Default(DocTest):
        saved = "s", func

    t = Default()
    assert t.saved == 1
    assert t == {Default.saved: 1}


def test_saved_default_memoizes_first_value_on_multiple_accesses():
    s = [0]

    def func():
        s[0] += 1
        return s[0]

    class Default(DocTest):
        saved = "s", func

    t = Default()
    assert t.saved == 1
    assert t.saved == 1
    assert s[0] == 1


def test_saved_default_is_inheritable():
    class Default(DocTest):
        saved = "s", lambda: 1

    class Sub(Default):
        other = "o", lambda: 2

    class Over(Default):
        saved = "s", lambda: 3

    d = Default()
    assert d.saved == 1

    d = Sub()
    assert d.saved == 1
    assert d.other == 2

    d = Over()
    assert d.saved == 3


def test_default_is_inheritable():
    class Default(DocTest):
        val = "s", 1

    class Sub(Default):
        other = "o", 2

    class Over(Default):
        val = "s", 3

    d = Default()
    assert d.val == 1

    d = Sub()
    assert d.val == 1
    assert d.other == 2

    d = Over()
    assert d.val == 3


def test_saved_default_is_set_on_saving():
    class Default(DocTest):
        saved = "s", lambda: 1

    d = Default()
    with DBTest:
        _id = Default.save(d, **_safe)
        d = Default.find_one(_id)

    d.pop("_id")
    assert dict(d) == {Default.saved: 1}


def test_saved_default_is_set_on_inserting():
    class Default(DocTest):
        saved = "s", lambda: 1

    d = Default()
    with DBTest:
        _id = Default.insert(d, **_safe)
        d = Default.find_one(_id)

    d.pop("_id")
    assert dict(d) == {Default.saved: 1}


def test_saved_default_is_set_on_multiple_inserts():
    class Default(DocTest):
        saved = "s", lambda: 1

    docs = []
    for i in range(3):
        d = Default()
        d._id = "test_saved_default_%s" % i
        docs.append(d)

    with DBTest:
        _ids = Default.insert(docs, **_safe)
        assert len(_ids) == 3
        docs = list(Default.find({Default._id: {"$in": _ids}}))

    assert len(docs) == 3
    for doc in docs:
        doc.pop("_id")
        assert dict(doc) == {Default.saved: 1}


def test_saved_defaults_are_set_in_json():
    class Default(DocTest):
        saved = "s", lambda: 1

    d = Default()
    assert d.for_json() == {"saved": 1}


def test_defaults_are_set_in_json_but_not_in_doc():
    class Default(DocTest):
        val = "v", 1

    d = Default()
    assert d.for_json() == {"val": 1}
    assert d.get(Default.val, None) is None


def test_saved_defaults_with_defaults_as_json():
    class Default(DocTest):
        saved = "s", lambda: 1
        val = "v", 2

    d = Default()
    assert d.for_json() == {"val": 2, "saved": 1}
    assert d.get(Default.val, None) is None
    assert d.saved == 1


def test_embedded_defaults_are_unmapped():
    with pytest.raises(AttributeError):

        class Embedded(DocTest):
            val = Embed("v")
            val.sub = "s", 1
            val.sub2 = "s"

        assert Embedded.val.sub == ("s", 1)
        assert Embedded.val.sub2 == "v.s"
        d = Embedded()
        d.val.sub  # This will raise AttributeError since val.sub is unmapped


def test_only_two_tuples_with_leading_string_are_interpreted_as_defaults():
    v1 = ("a",)
    v2 = ("b", 2)
    v3 = ("c", 3, 4)
    v4 = (1, 2)

    class TupleTest(DocTest):
        attr1 = v1
        attr2 = v2
        attr3 = v3
        attr4 = v4

    assert TupleTest.attr1 == v1
    assert TupleTest.attr2 == "b"
    assert TupleTest.attr3 == v3
    assert TupleTest.attr4 == v4
    d = TupleTest()
    assert d.attr1 == v1
    assert d.attr2 == 2
    assert d.attr3 == v3
    assert d.attr4 == v4


def test_update_with_safe_keyword_doesnt_break_pymongo_3():
    with DBTest:
        DocTest.update(
            {"_id": "update_safe_pymongo_3"},
            {"$set": {"ok": True}},
            upsert=True,
            safe=True,
        )


def test_save_with_safe_keyword_doesnt_break_pymongo_3():
    with DBTest:
        DocTest.save({"_id": "save_safe_pymongo_3"}, safe=True)


def test_insert_with_safe_keyword_doesnt_break_pymongo_3():
    with DBTest:
        DocTest.insert({"_id": "insert_safe_pymongo_3"}, safe=True)
