import random

from six.moves import xrange

from humbledb import Document
from humbledb.array import Array
from test.util import (database_name, DBTest, ok_, eq_, enable_sharding,
        SkipTest, raises)


class TestArray(Array):
    config_database = database_name()
    config_collection = 'arrays'
    config_max_size = 3
    config_padding = 100


def teardown():
    DBTest.connection.drop_database(database_name())


def _word():
    """ Return a random "word". """
    return str(random.randint(1, 15000))


def test_document_without_configuration_works_as_mapper():
    class Entry(Document):
        name = 'n'
        display = 'd'

    entry = Entry()
    entry.name = "Test"
    eq_(entry, {Entry.name: "Test"})
    eq_(entry.for_json(), {u'name': 'Test'})


def test_creates_a_new_page_on_first_insert():
    t = TestArray('new_page', 0)
    with DBTest:
        t.append("Test")
        eq_(t.pages(), 1)


def test_all_returns_single_insert_ok():
    t = TestArray('single_insert', 0)
    v = "Test"
    with DBTest:
        eq_(t.append(v), 1)
        eq_(t.all(), [v])


def test_appends_over_max_size_creates_second_page():
    t = TestArray('appends_second_page', 0)
    with DBTest:
        eq_(t.append(_word()), 1)
        eq_(t.append(_word()), 1)
        eq_(t.append(_word()), 2)
        eq_(t.append(_word()), 2)
        eq_(t.pages(), 2)
        eq_(len(t.all()), 4)


def test_multiple_appends_with_zero_pages_works_ok():
    t = TestArray('zero_pages', 0)
    with DBTest:
        eq_(t.append(_word()), 1)
    t = TestArray('zero_pages', 0)
    with DBTest:
        eq_(t.append(_word()), 1)
        eq_(len(t.all()), 2)


def test_length_for_single_page_works():
    t = TestArray('length_single', 0)
    with DBTest:
        t.append(_word())
        eq_(t.length(), 1)
        t.append(_word())
        eq_(t.length(), 2)
        t.append(_word())
        eq_(t.length(), 3)


def test_length_for_multiple_pages_works():
    t = TestArray('length_multi', 0)
    with DBTest:
        for i in xrange(10):
            t.append(_word())
        eq_(t.length(), 10)
        eq_(t.pages(), 4)


def test_remove_works_with_single_page():
    t = TestArray('remove', 0)
    v = "Test"
    with DBTest:
        t.append(_word())
        t.append(v)
        t.append(_word())
        eq_(t.length(), 3)
        t.remove(v)
        eq_(t.length(), 2)


def test_remove_works_with_multiple_pages():
    t = TestArray('remove_multi_page', 0)
    v = "Test"
    with DBTest:
        for i in xrange(5):
            t.append(_word())
        t.append(v)
        for i in xrange(5):
            t.append(_word())
        eq_(t.length(), 11)
        ok_(v in t.all())
        t.remove(v)
        eq_(t.length(), 10)
        ok_(v not in t.all())


def test_remove_works_with_embedded_documents():
    t = TestArray('remove_embedded_docs')
    with DBTest:
        for i in xrange(5):
            t.append({'i': i, 'k': i})
        eq_(t.length(), 5)
        t.remove({'i': 3})
        eq_(t.length(), 4)


def test_remove_works_with_complex_embedded_documents_and_dot_notation():
    t = TestArray('remove_complex_embedded_docs')
    with DBTest:
        for i in xrange(5):
            t.append({'foo': 'bar', 'fnord': {'i': i, 'spam': 'eggs'}})
        eq_(t.length(), 5)
        ok_(t.remove({'fnord.i': 3}))
        eq_(t.length(), 4)


def test_multiple_removes_maintains_correct_count_with_dupes_on_diff_pages():
    t = TestArray('remove_count')
    with DBTest:
        t.append({'i': 9})
        for i in xrange(3):
            t.append({'i': i})
        t.append({'i': 9})
        t.remove({'i': 9})
        pages = list(TestArray.find({'_id': t._id_regex}))
        for page in pages:
            eq_(page.size, len(page.entries))


def test_multiple_removes_maintains_correct_count_with_dupes_on_same_page():
    t = TestArray('remove_count_dupes')
    with DBTest:
        for i in xrange(3):
            t.append({'i': i})
        t.append({'i': 9})
        t.append({'i': 9})
        eq_(t.length(), 5)
        t.remove({'i': 9})
        eq_(t.length(), 4)
        pages = list(TestArray.find({'_id': t._id_regex}))
        for page in pages:
            eq_(page.size, len(page.entries))
        t.remove({'i': 9})
        eq_(t.length(), 3)
        pages = list(TestArray.find({'_id': t._id_regex}))
        for page in pages:
            eq_(page.size, len(page.entries))
        t.remove({'i': 9})
        eq_(t.length(), 3)


def test_remove_one_more_time_just_for_kicks():
    t = TestArray('never_stop_testing_remove')
    with DBTest:
        for i in xrange(10):
            t.append(i)
        eq_(t[:], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        eq_(t.length(), 10)
        t.remove(2)
        eq_(t[0:], [0, 1, 3, 4, 5, 6, 7, 8, 9])
        eq_(t.length(), 9)
        t.remove(9)
        eq_(t[:3], [0, 1, 3, 4, 5, 6, 7, 8])
        eq_(t.length(), 8)


def test_sharded_remove_works():
    t = TestArray('test_sharded_remove')
    if not enable_sharding(TestArray._page.config_collection, {'_id': 1}):
        raise SkipTest
    with DBTest:
        for word in "The quick brown fox jumps over the lazy dog.".split():
            t.append(word)
        eq_(t.length(), 9)
        eq_(t.pages(), 4)
        eq_(t[3], [])
        t.remove('lazy')
        eq_(t.length(), 8)
        eq_(t[2], ['the', 'dog.'])
        t.remove('fox')
        eq_(t.length(), 7)
        eq_(t[1], ['jumps', 'over'])


def test_sharded_remove_works_with_embedded_documents():
    t = TestArray('test_sharded_remove_embedded')
    if not enable_sharding(TestArray._page.config_collection, {'_id': 1}):
        raise SkipTest
    with DBTest:
        for word in "The quick brown fox jumps over the lazy dog.".split():
            t.append({'word': word})
        eq_(t.length(), 9)
        eq_(t.pages(), 4)
        eq_(t[3], [])
        t.remove({'word': 'lazy'})
        eq_(t.length(), 8)
        eq_(t[2], [{'word': 'the'}, {'word': 'dog.'}])
        t.remove({'word': 'fox'})
        eq_(t.length(), 7)
        eq_(t[1], [{'word': 'jumps'}, {'word': 'over'}])


@raises(TypeError)
def test_class_errors_if_missing_database():
    class Test(Array):
        config_collection = 'c'


@raises(TypeError)
def test_class_errors_if_missing_collection():
    class Test(Array):
        config_database = 'd'


@raises(RuntimeError)
def test_append_fails_if_page_is_missing():
    t = TestArray('append_fails_with_missing_page', 0)
    with DBTest:
        t.append(1)
        t._page.remove({t._page._id: t._id_regex})
        t.append(1)


def test_clear_removes_all_pages():
    t = TestArray('clear', 0)
    with DBTest:
        for i in xrange(10):
            t.append(_word())
        eq_(t.length(), 10)
        eq_(t.pages(), 4)
        t.clear()
        eq_(t.length(), 0)
        eq_(t.pages(), 0)


def test_append_works_after_clearing():
    t = TestArray('clear_and_append', 0)
    with DBTest:
        for i in xrange(10):
            t.append(_word())
        eq_(t.length(), 10)
        eq_(t.pages(), 4)
        t.clear()
        eq_(t.length(), 0)
        eq_(t.pages(), 0)
        t.append(1)
        eq_(t.length(), 1)
        eq_(t.pages(), 1)


def test_getitem_works_for_single_page():
    t = TestArray('getitem_single', 0)
    with DBTest:
        for i in xrange(10):
            t.append(i)
        eq_(t.pages(), 4)
        eq_(t[0], [0, 1, 2])
        eq_(t[1], [3, 4, 5])
        eq_(t[2], [6, 7, 8])
        eq_(t[3], [9])


def test_getitem_works_for_slices():
    t = TestArray('getitem_sliced', 0)
    with DBTest:
        for i in xrange(10):
            t.append(i)
        eq_(t.pages(), 4)
        eq_(t[0:1], [0, 1, 2])
        eq_(t[1:2], [3, 4, 5])
        eq_(t[0:2], [0, 1, 2, 3, 4, 5])
        eq_(t[2:4], [6, 7, 8, 9])
        eq_(t[0:100], list(range(10)))


@raises(TypeError)
def test_getitem_does_not_work_for_extended_slices():
    t = TestArray('test', 0)
    t[0:1:2]


@raises(TypeError)
def test_getitem_disallows_non_integers():
    t = TestArray('test', 0)
    t['foo']


@raises(IndexError)
def test_getitem_raises_indexerror_for_out_of_range_when_empty():
    t = TestArray('getitem_out_of_range_empty', 0)
    with DBTest:
        t[0]


@raises(IndexError)
def test_getitem_raises_indexerror_for_out_of_range():
    t = TestArray('getitem_out_of_range', 0)
    with DBTest:
        for i in xrange(10):
            t.append(i)
        ok_(t[0])
        ok_(t[1])
        ok_(t[2])
        ok_(t[3])
        t[4]


def test_find_gives_us_a_working_find():
    t = TestArray('find', 0)
    with DBTest:
        eq_(list(TestArray.find({'_id': t._id_regex})), [])


def test_entries_returns_key_on_class():
    t = TestArray('entries', 0)
    with DBTest:
        eq_(TestArray.entries, t._page.entries)
        eq_(TestArray.entries, TestArray._page.entries)
        eq_(TestArray.entries, 'e')


def test_size_returns_key_on_class():
    t = TestArray('size', 0)
    with DBTest:
        eq_(TestArray.size, t._page.size)
        eq_(TestArray.size, TestArray._page.size)
        eq_(TestArray.size, 's')


def test_unset_page_count_queries_for_the_page_count():
    t = TestArray('unset_page_count', 0)
    with DBTest:
        for i in xrange(6):
            t.append(i)
        t2 = TestArray('unset_page_count')
        t2.append(7)
        eq_(t.pages(), t2.page_count)
        eq_(t2.page_count, 3)
        eq_(t[2], [7])


def test_all_returns_unmapped_entries():
    t = TestArray('all_unmapped')
    with DBTest:
        for i in xrange(3):
            t.append({str(i): i})

        for o in t.all():
            eq_(type(o), dict)


def test_iteration():
    t = TestArray('iteration')
    with DBTest:
        l = set(xrange(15))
        for i in l:
            t.append(i)
        for page in t:
            if not page:
                break
            eq_(len(page), 3)
            for e in page:
                l.remove(e)
        eq_(l, set())


def test_array_regex_ignores_dots():
    t = TestArray('with.dot')
    t2 = TestArray('with_dot')

    with DBTest:
        t.append(1)
        t2.append(2)

        eq_(t.all(), [1])
        eq_(t2.all(), [2])

