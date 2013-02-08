from ..util import *
from humbledb import Document, Embed


def teardown():
    DBTest.connection.drop_database(database_name())


class MapTest(Document):
    em = Embed('e')
    em.val = 'v'
    val = 'v'


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

    eq_(sorted(TestMapped.mapped_attributes()), ['embed', 'key1', 'key2',
        'key3'])


def test_embed_non_string_values_are_not_mapped():
    class TestMapped(Document):
        embed = Embed('e')
        embed.good = 'g'
        embed.bad = True

    eq_(TestMapped.embed.good, 'e.g')
    eq_(getattr(TestMapped.embed, 'bad', -1), -1)


def test_embed_private_values_are_not_mapped():
    class TestMapped(Document):
        embed = Embed('e')
        embed.good = 'g'
        embed._bad = 'b'

    eq_(TestMapped.embed.good, 'e.g')
    eq_(getattr(TestMapped.embed, '_bad', -1), -1)


@raises(AttributeError)
def test_bad_embedded_mappings_raise_an_attribute_error_on_the_instance():
    class Test(Document):
        embed = Embed('e')
        embed.mapped = 'm'

    # This will raise an attribute error
    Test().embed.not_mapped


def test_embedded_key_retrieval_on_instance_is_none():
    eq_(MapTest().em.val, {})


def test_missing_key_retrieval_is_none():
    eq_(MapTest().val, {})


@raises(AttributeError)
def test_unmapped_attribute_assignment_to_dict_map_is_an_error():
    t = MapTest()
    t.em.foo = 'bar'


def test_deleting_an_unmapped_attribute_from_dict_map_works():
    t = MapTest()
    em = t.em
    object.__setattr__(em, 'foo', True)
    del em.foo

    is_(getattr(em, 'foo', None), None)


@raises(AttributeError)
def test_deleting_an_unset_mapped_attribute_from_dict_map_is_an_error():
    t = MapTest()
    em = t.em
    del em.val


def test_deleting_a_subkey_when_unset_is_harmless():
    t = MapTest()
    del t.em['v']


@raises(KeyError)
def test_deleting_a_missing_key_is_an_error():
    t = MapTest()
    t.val = {}
    del t.val['k']


def test_deleting_the_last_key_removes_an_embedded_doc():
    t = MapTest()
    t.val = {'a': 1}
    eq_(t, {'v': {'a': 1}})
    del t.val['a']
    eq_(t, {})
