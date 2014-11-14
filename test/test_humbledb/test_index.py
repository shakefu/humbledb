
import mock
import pyconfig

import humbledb
from ..util import *
from humbledb import Document, Embed, Index, _version


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


def test_index_basic():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'
        config_indexes = [Index('user_name')]

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


def test_index_basic_sparse():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'
        config_indexes = [Index('user_name', sparse=True)]

        user_name = 'u'

    with DBTest:
        with mock.patch.object(Test, 'collection') as coll:
            coll.find_one.__name__ = 'find_one'
            Test._ensured = None
            Test.find_one()
            coll.ensure_index.assert_called_with(
                    Test.user_name,
                    background=True,
                    sparse=True,
                    **cache_for(60*60*24))


def test_index_basic_directional():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'
        config_indexes = [Index([('user_name', humbledb.DESC)])]

        user_name = 'u'

    with DBTest:
        with mock.patch.object(Test, 'collection') as coll:
            coll.find_one.__name__ = 'find_one'
            Test._ensured = None
            Test.find_one()
            coll.ensure_index.assert_called_with(
                    [(Test.user_name, humbledb.DESC)],
                    background=True,
                    **cache_for(60*60*24))


def test_index_override_defaults():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'
        config_indexes = [Index('user_name', background=False, cache_for=60)]

        user_name = 'u'

    with DBTest:
        with mock.patch.object(Test, 'collection') as coll:
            coll.find_one.__name__ = 'find_one'
            Test._ensured = None
            Test.find_one()
            coll.ensure_index.assert_called_with(
                    Test.user_name,
                    background=False,
                    **cache_for(60))


def test_resolve_dotted_index():
    class TestResolveIndex(DocTest):
        meta = Embed('m')
        meta.tag = 't'

    eq_(Index('meta')._resolve_index(TestResolveIndex), 'm')
    eq_(Index('meta.tag')._resolve_index(TestResolveIndex), 'm.t')
    eq_(Index('meta.foo')._resolve_index(TestResolveIndex), 'meta.foo')


def test_resolve_deep_dotted_index():
    class TestResolveIndex(DocTest):
        meta = Embed('m')
        meta.deep = Embed('d')
        meta.deep.deeper = Embed('d')
        meta.deep.deeper.deeper_still = Embed('d')
        meta.deep.deeper.deeper_still.tag = 't'

    eq_(Index('meta.deep')._resolve_index(TestResolveIndex), 'm.d')
    eq_(Index('meta.deep.deeper')._resolve_index(TestResolveIndex), 'm.d.d')
    eq_(Index('meta.deep.deeper.deeper_still')._resolve_index(
        TestResolveIndex), 'm.d.d.d')
    eq_(Index('meta.deep.deeper.deeper_still.tag')._resolve_index(
        TestResolveIndex), 'm.d.d.d.t')


def test_resolve_compound_index():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'
        config_indexes = [Index([('user_name', humbledb.ASC), ('compound',
            humbledb.DESC)])]

        user_name = 'u'
        compound = 'c'

    with DBTest:
        # This will raise a TypeError
        with mock.patch.object(Test, 'collection') as coll:
            coll.find_one.__name__ = 'find_one'
            Test._ensured = None
            Test.find_one()
            coll.ensure_index.assert_called_with(
                    [(Test.user_name, humbledb.ASC), (Test.compound,
                        humbledb.DESC)],
                    background=True,
                    **cache_for(60*60*24))


@raises(TypeError)
def test_resolve_non_string_attribute_fails():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'
        config_indexes = [Index('value')]

        value = True

    with DBTest:
        # This will raise a TypeError
        with mock.patch.object(Test, 'collection') as coll:
            coll.find_one.__name__ = 'find_one'
            Test._ensured = None
            Test.find_one()
            coll.ensure_index.assert_not_called()


@raises(TypeError)
def test_badly_formed_index_raises_error():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'
        config_indexes = [Index([('value',)])]

    with DBTest:
        # This will raise a TypeError
        with mock.patch.object(Test, 'collection') as coll:
            coll.find_one.__name__ = 'find_one'
            Test._ensured = None
            Test.find_one()
            eq_(coll.ensure_index.called, False)


def test_ensure_index_can_be_skipped():
    class Test(Document):
        config_database = database_name()
        config_collection = 'test'
        config_indexes = [Index('value')]
        value = 'v'

    with DBTest:
        with mock.patch.object(Test, 'collection') as coll:
            coll.find_one.__name__ = 'find_one'
            pyconfig.set('humbledb.ensure_indexes', False)
            Test.find_one()
            pyconfig.set('humbledb.ensure_indexes', True)
            eq_(coll.ensure_index.called, False)


