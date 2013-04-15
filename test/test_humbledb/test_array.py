import random
from unittest.case import SkipTest

from test.util import *
from humbledb import Document
from humbledb.array import Array


class TestArray(Array):
    config_database = database_name()
    config_collection = 'arrays'
    config_max_size = 3


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
    eq_(entry._asdict(), {u'name': 'Test'})


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
        t._page.remove({t._page.array_id: t.array_id})
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
        eq_(t[0:100], range(10))


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
