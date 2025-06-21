import mock
import pyconfig
import pytest

import humbledb
from humbledb import Document, Embed, Index, _version

from ..util import DBTest, database_name


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


def test_index_basic():
    if _version._gte("4.0"):
        pytest.skip("ensure_index was removed in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [Index("user_name")]

        user_name = "u"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.ensure_index.assert_called_with(
                Test.user_name, background=True, **cache_for(60 * 60 * 24)
            )


def test_index_basic_sparse():
    if _version._gte("4.0"):
        pytest.skip("ensure_index was removed in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [Index("user_name", sparse=True)]

        user_name = "u"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.ensure_index.assert_called_with(
                Test.user_name, background=True, sparse=True, **cache_for(60 * 60 * 24)
            )


def test_index_basic_directional():
    if _version._gte("4.0"):
        pytest.skip("ensure_index was removed in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [Index([("user_name", humbledb.DESC)])]

        user_name = "u"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.ensure_index.assert_called_with(
                [(Test.user_name, humbledb.DESC)],
                background=True,
                **cache_for(60 * 60 * 24),
            )


def test_index_override_defaults():
    if _version._gte("4.0"):
        pytest.skip("ensure_index was removed in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [Index("user_name", background=False, cache_for=60)]

        user_name = "u"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.ensure_index.assert_called_with(
                Test.user_name, background=False, **cache_for(60)
            )


def test_resolve_dotted_index():
    class TestResolveIndex(DocTest):
        meta = Embed("m")
        meta.tag = "t"

    assert Index("meta")._resolve_index(TestResolveIndex) == "m"
    assert Index("meta.tag")._resolve_index(TestResolveIndex) == "m.t"
    assert Index("meta.foo")._resolve_index(TestResolveIndex) == "meta.foo"


def test_resolve_deep_dotted_index():
    class TestResolveIndex(DocTest):
        meta = Embed("m")
        meta.deep = Embed("d")
        meta.deep.deeper = Embed("d")
        meta.deep.deeper.deeper_still = Embed("d")
        meta.deep.deeper.deeper_still.tag = "t"

    assert Index("meta.deep")._resolve_index(TestResolveIndex) == "m.d"
    assert Index("meta.deep.deeper")._resolve_index(TestResolveIndex) == "m.d.d"
    assert (
        Index("meta.deep.deeper.deeper_still")._resolve_index(TestResolveIndex)
        == "m.d.d.d"
    )
    assert (
        Index("meta.deep.deeper.deeper_still.tag")._resolve_index(TestResolveIndex)
        == "m.d.d.d.t"
    )


def test_resolve_compound_index():
    if _version._gte("4.0"):
        pytest.skip("ensure_index was removed in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [
            Index([("user_name", humbledb.ASC), ("compound", humbledb.DESC)])
        ]

        user_name = "u"
        compound = "c"

    with DBTest:
        # This will raise a TypeError
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.ensure_index.assert_called_with(
                [(Test.user_name, humbledb.ASC), (Test.compound, humbledb.DESC)],
                background=True,
                **cache_for(60 * 60 * 24),
            )


def test_resolve_non_string_attribute_fails():
    if _version._gte("4.0"):
        pytest.skip("ensure_index was removed in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [Index("value")]

        value = True

    with DBTest:
        # This will raise a TypeError
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            with pytest.raises(TypeError):
                Test.find_one()
            coll.ensure_index.assert_not_called()


def test_badly_formed_index_raises_error():
    if _version._gte("4.0"):
        pytest.skip("ensure_index was removed in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [Index([("value",)])]

    with DBTest:
        # This will raise a TypeError
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            with pytest.raises(TypeError):
                Test.find_one()
            assert not coll.ensure_index.called


def test_ensure_index_can_be_skipped():
    if _version._gte("4.0"):
        pytest.skip("ensure_index was removed in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [Index("value")]
        value = "v"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            pyconfig.set("humbledb.ensure_indexes", False)
            Test.find_one()
            pyconfig.set("humbledb.ensure_indexes", True)
            assert not coll.ensure_index.called


def test_index_basic_pymongo_4():
    if _version._lt("4.0"):
        pytest.skip("create_index was introduced in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [Index("user_name")]

        user_name = "u"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.create_index.assert_called_with(Test.user_name, background=True)


def test_index_basic_sparse_pymongo_4():
    if _version._lt("4.0"):
        pytest.skip("create_index was introduced in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [Index("user_name", sparse=True)]

        user_name = "u"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.create_index.assert_called_with(
                Test.user_name, background=True, sparse=True
            )


def test_index_basic_directional_pymongo_4():
    if _version._lt("4.0"):
        pytest.skip("create_index was introduced in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [Index([("user_name", humbledb.DESC)])]

        user_name = "u"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.create_index.assert_called_with(
                [(Test.user_name, humbledb.DESC)],
                background=True,
            )


def test_index_override_defaults_pymongo_4():
    if _version._lt("4.0"):
        pytest.skip("create_index was introduced in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [Index("user_name", background=False, cache_for=60)]

        user_name = "u"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.create_index.assert_called_with(Test.user_name, background=False)


def test_resolve_compound_index_pymongo_4():
    if _version._lt("4.0"):
        pytest.skip("create_index was introduced in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [
            Index([("user_name", humbledb.ASC), ("compound", humbledb.DESC)])
        ]

        user_name = "u"
        compound = "c"

    with DBTest:
        # This will raise a TypeError
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            Test._ensured = None
            Test.find_one()
            coll.create_index.assert_called_with(
                [(Test.user_name, humbledb.ASC), (Test.compound, humbledb.DESC)],
                background=True,
            )


def test_resolve_non_string_attribute_fails_pymongo_4():
    if _version._lt("4.0"):
        pytest.skip("create_index was introduced in Pymongo 4.x")

    with pytest.raises(TypeError):

        class Test(Document):
            config_database = database_name()
            config_collection = "test"
            config_indexes = [Index("value")]

            value = True


def test_badly_formed_index_raises_error_pymongo_4():
    if _version._lt("4.0"):
        pytest.skip("create_index was introduced in Pymongo 4.x")

    with pytest.raises(TypeError):

        class Test(Document):
            config_database = database_name()
            config_collection = "test"
            config_indexes = [Index([("value",)])]


def test_create_index_can_be_skipped_pymongo_4():
    if _version._lt("4.0"):
        pytest.skip("create_index was introduced in Pymongo 4.x")

    class Test(Document):
        config_database = database_name()
        config_collection = "test"
        config_indexes = [Index("value")]
        value = "v"

    with DBTest:
        with mock.patch.object(Test, "collection") as coll:
            coll.find_one.__name__ = "find_one"
            pyconfig.set("humbledb.ensure_indexes", False)
            Test.find_one()
            pyconfig.set("humbledb.ensure_indexes", True)
            assert not coll.create_index.called
