from ..util import *
from humbledb.maps import ListMap
from humbledb import Document, Embed


def teardown():
    DBTest.connection.drop_database(database_name())


class MapTest(Document):
    em = Embed('e')
    em.val = 'v'
    val = 'v'


class DocTest(Document):
    config_database = database_name()
    config_collection = 'doc_test'


class ListTest(DocTest):
    vals = Embed('l')
    vals.one = 'o'
    vals.two = 't'


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


def test_lists_are_mapped():
    doc = ListTest()
    doc.vals = ['hello', 'world']
    with DBTest:
        ListTest.insert(doc)
        doc = ListTest.find_one()
    is_instance_(doc.vals, ListMap)


def test_embedded_list_as_json_replaces_embedded_doc_field_names():
    doc = ListTest()
    doc.vals = [{'o': 'hello'}, 'world']
    eq_(doc._asdict(), {'vals': [{'one': 'hello'}, 'world']})


def test_embedded_list_as_json_recursively_sets_field_names():
    class Test(DocTest):
        vals = Embed('l')
        vals.one = 'o'
        vals.sub = Embed('s')
        vals.sub.two = 't'

    doc = Test()
    doc.vals = [{'s': [{'t': 'hello'}], 'o': 1}, {'o': 1}]
    eq_(doc._asdict(), {'vals': [{'sub': [{'two': 'hello'}], 'one': 1},
        {'one': 1}]})


def test_embedded_list_creation_with_attributes():
    class Test(DocTest):
        vals = Embed('l')
        vals.one = 'o'
        vals.two = 't'

    doc = Test()
    doc.vals = []
    val = doc.vals.new()
    val.one = 1
    val.two = 2
    eq_(doc._asdict(), {'vals': [{'one': 1, 'two': 2}]})


def test_embedded_list_with_crazy_complex_heirarchy():
    class Test(DocTest):
        s1 = 's1'
        l1 = Embed('l1')
        l1.s2 = 's2'
        l1.l2 = Embed('l2')
        l1.l2.s3 = 's3'

    doc = Test()
    doc.l1 = []
    doc.s1 = 1
    item = doc.l1.new()
    item.l2 = []
    item.s2 = 2
    item2 = item.l2.new()
    item2.s3 = 3

    eq_(doc, {'s1': 1, 'l1':[{'s2': 2, 'l2': [{'s3': 3}]}]})

    with DBTest:
        doc_id = Test.insert(doc)
        doc = Test.find_one({Test._id: doc_id})

    doc.pop('_id')
    eq_(doc, {'s1': 1, 'l1':[{'s2': 2, 'l2': [{'s3': 3}]}]})


def test_embedded_list_iteration():
    class Test(DocTest):
        vals = Embed('v')
        vals.i = 'i'

    doc = Test()
    doc.vals = []
    for i in xrange(5):
        item = doc.vals.new()
        item.i = i

    for item in doc.vals:
        is_instance_(item.i, int)

    for i in xrange(len(doc.vals)):
        is_instance_(item.i, int)


def test_modified_items_save_ok():
    class Test(DocTest):
        vals = Embed('v')
        vals.i = 'i'

    doc = Test()
    doc.vals = []
    for i in xrange(5):
        item = doc.vals.new()
        item.i = i

    with DBTest:
        doc_id = Test.insert(doc)
        doc = Test.find_one({Test._id: doc_id})

    for item in doc.vals:
        item.i = 12

    with DBTest:
        Test.save(doc)
        doc = Test.find_one({Test._id: doc_id})

    eq_(len(doc.vals), 5)

    total = 0
    for item in doc.vals:
        eq_(item.i, 12)
        total += item.i

    eq_(total, 60)
