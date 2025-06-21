import random

import pytest

from humbledb import Document
from humbledb.array import Array

from ..util import database_name


class ArrayTest(Array):
    config_database = database_name()
    config_collection = "arrays"
    config_max_size = 3
    config_padding = 100


def _word():
    """Return a random "word"."""
    return str(random.randint(1, 15000))


def test_document_without_configuration_works_as_mapper():
    class Entry(Document):
        name = "n"
        display = "d"

    entry = Entry()
    entry.name = "Test"
    assert entry == {Entry.name: "Test"}
    assert entry.for_json() == {"name": "Test"}


def test_creates_a_new_page_on_first_insert(DBTest):
    t = ArrayTest("new_page", 0)
    with DBTest:
        t.append("Test")
        assert t.pages() == 1


def test_all_returns_single_insert_ok(DBTest):
    t = ArrayTest("single_insert", 0)
    v = "Test"
    with DBTest:
        assert t.append(v) == 1
        assert t.all() == [v]


def test_appends_over_max_size_creates_second_page(DBTest):
    t = ArrayTest("appends_second_page", 0)
    with DBTest:
        assert t.append(_word()) == 1
        assert t.append(_word()) == 1
        assert t.append(_word()) == 2
        assert t.append(_word()) == 2
        assert t.pages() == 2
        assert len(t.all()) == 4


def test_multiple_appends_with_zero_pages_works_ok(DBTest):
    t = ArrayTest("zero_pages", 0)
    with DBTest:
        assert t.append(_word()) == 1
    t = ArrayTest("zero_pages", 0)
    with DBTest:
        assert t.append(_word()) == 1
        assert len(t.all()) == 2


def test_length_for_single_page_works(DBTest):
    t = ArrayTest("length_single", 0)
    with DBTest:
        t.append(_word())
        assert t.length() == 1
        t.append(_word())
        assert t.length() == 2
        t.append(_word())
        assert t.length() == 3


def test_length_for_multiple_pages_works(DBTest):
    t = ArrayTest("length_multi", 0)
    with DBTest:
        for i in range(10):
            t.append(_word())
        assert t.length() == 10
        assert t.pages() == 4


def test_remove_works_with_single_page(DBTest):
    t = ArrayTest("remove", 0)
    v = "Test"
    with DBTest:
        t.append(_word())
        t.append(v)
        t.append(_word())
        assert t.length() == 3
        t.remove(v)
        assert t.length() == 2


def test_remove_works_with_multiple_pages(DBTest):
    t = ArrayTest("remove_multi_page", 0)
    v = "Test"
    with DBTest:
        for i in range(5):
            t.append(_word())
        t.append(v)
        for i in range(5):
            t.append(_word())
        assert t.length() == 11
        assert v in t.all()
        t.remove(v)
        assert t.length() == 10
        assert v not in t.all()


def test_remove_works_with_embedded_documents(DBTest):
    t = ArrayTest("remove_embedded_docs")
    with DBTest:
        for i in range(5):
            t.append({"i": i, "k": i})
        assert t.length() == 5
        t.remove({"i": 3})
        assert t.length() == 4


def test_remove_works_with_complex_embedded_documents_and_dot_notation(DBTest):
    t = ArrayTest("remove_complex_embedded_docs")
    with DBTest:
        for i in range(5):
            t.append({"foo": "bar", "fnord": {"i": i, "spam": "eggs"}})
        assert t.length() == 5
        assert t.remove({"fnord.i": 3})
        assert t.length() == 4


def test_multiple_removes_maintains_correct_count_with_dupes_on_diff_pages(DBTest):
    t = ArrayTest("remove_count")
    with DBTest:
        t.append({"i": 9})
        for i in range(3):
            t.append({"i": i})
        t.append({"i": 9})
        t.remove({"i": 9})
        pages = list(ArrayTest.find({"_id": t._id_regex}))
        for page in pages:
            assert page.size == len(page.entries)


def test_multiple_removes_maintains_correct_count_with_dupes_on_same_page(DBTest):
    t = ArrayTest("remove_count_dupes")
    with DBTest:
        for i in range(3):
            t.append({"i": i})
        t.append({"i": 9})
        t.append({"i": 9})
        assert t.length() == 5
        t.remove({"i": 9})
        assert t.length() == 4
        pages = list(ArrayTest.find({"_id": t._id_regex}))
        for page in pages:
            assert page.size == len(page.entries)
        t.remove({"i": 9})
        assert t.length() == 3
        pages = list(ArrayTest.find({"_id": t._id_regex}))
        for page in pages:
            assert page.size == len(page.entries)
        t.remove({"i": 9})
        assert t.length() == 3


def test_remove_one_more_time_just_for_kicks(DBTest):
    t = ArrayTest("never_stop_testing_remove")
    with DBTest:
        for i in range(10):
            t.append(i)
        assert t[:] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        assert t.length() == 10
        t.remove(2)
        assert t[0:] == [0, 1, 3, 4, 5, 6, 7, 8, 9]
        assert t.length() == 9
        t.remove(9)
        assert t[:3] == [0, 1, 3, 4, 5, 6, 7, 8]
        assert t.length() == 8


def test_sharded_remove_works(DBTest, enable_sharding):
    t = ArrayTest("test_sharded_remove")
    if not enable_sharding(ArrayTest._page.config_collection, {"_id": 1}):
        pytest.skip("Sharding not enabled")
    with DBTest:
        for word in "The quick brown fox jumps over the lazy dog.".split():
            t.append(word)
        assert t.length() == 9
        assert t.pages() == 4
        assert t[3] == []
        t.remove("lazy")
        assert t.length() == 8
        assert t[2] == ["the", "dog."]
        t.remove("fox")
        assert t.length() == 7
        assert t[1] == ["jumps", "over"]


def test_sharded_remove_works_with_embedded_documents(DBTest, enable_sharding):
    t = ArrayTest("test_sharded_remove_embedded")
    if not enable_sharding(ArrayTest._page.config_collection, {"_id": 1}):
        pytest.skip("Sharding not enabled")
    with DBTest:
        for word in "The quick brown fox jumps over the lazy dog.".split():
            t.append({"word": word})
        assert t.length() == 9
        assert t.pages() == 4
        assert t[3] == []
        t.remove({"word": "lazy"})
        assert t.length() == 8
        assert t[2] == [{"word": "the"}, {"word": "dog."}]
        t.remove({"word": "fox"})
        assert t.length() == 7
        assert t[1] == [{"word": "jumps"}, {"word": "over"}]


def test_class_errors_if_missing_database():
    with pytest.raises(TypeError):

        class Test(Array):
            config_collection = "c"


def test_class_errors_if_missing_collection():
    with pytest.raises(TypeError):

        class Test(Array):
            config_database = "d"


def test_append_fails_if_page_is_missing(DBTest):
    t = ArrayTest("append_fails_with_missing_page", 0)
    with DBTest:
        t.append(1)
        t._page.remove({t._page._id: t._id_regex})
        with pytest.raises(RuntimeError):
            t.append(1)


def test_clear_removes_all_pages(DBTest):
    t = ArrayTest("clear", 0)
    with DBTest:
        for i in range(10):
            t.append(_word())
        assert t.length() == 10
        assert t.pages() == 4
        t.clear()
        assert t.length() == 0
        assert t.pages() == 0


def test_append_works_after_clearing(DBTest):
    t = ArrayTest("clear_and_append", 0)
    with DBTest:
        for i in range(10):
            t.append(_word())
        assert t.length() == 10
        assert t.pages() == 4
        t.clear()
        assert t.length() == 0
        assert t.pages() == 0
        t.append(1)
        assert t.length() == 1
        assert t.pages() == 1


def test_getitem_works_for_single_page(DBTest):
    t = ArrayTest("getitem_single", 0)
    with DBTest:
        for i in range(10):
            t.append(i)
        assert t.pages() == 4
        assert t[0] == [0, 1, 2]
        assert t[1] == [3, 4, 5]
        assert t[2] == [6, 7, 8]
        assert t[3] == [9]


def test_getitem_works_for_slices(DBTest):
    t = ArrayTest("getitem_sliced", 0)
    with DBTest:
        for i in range(10):
            t.append(i)
        assert t.pages() == 4
        assert t[0:1] == [0, 1, 2]
        assert t[1:2] == [3, 4, 5]
        assert t[0:2] == [0, 1, 2, 3, 4, 5]
        assert t[2:4] == [6, 7, 8, 9]
        assert t[0:100] == list(range(10))


def test_getitem_does_not_work_for_extended_slices():
    t = ArrayTest("test", 0)
    with pytest.raises(TypeError):
        t[0:1:2]


def test_getitem_disallows_non_integers():
    t = ArrayTest("test", 0)
    with pytest.raises(TypeError):
        t["foo"]


def test_getitem_raises_indexerror_for_out_of_range_when_empty(DBTest):
    t = ArrayTest("getitem_out_of_range_empty", 0)
    with DBTest:
        with pytest.raises(IndexError):
            t[0]


def test_getitem_raises_indexerror_for_out_of_range(DBTest):
    t = ArrayTest("getitem_out_of_range", 0)
    with DBTest:
        for i in range(10):
            t.append(i)
        assert t[0]
        assert t[1]
        assert t[2]
        assert t[3]
        with pytest.raises(IndexError):
            t[4]


def test_find_gives_us_a_working_find(DBTest):
    t = ArrayTest("find", 0)
    with DBTest:
        assert list(ArrayTest.find({"_id": t._id_regex})) == []


def test_entries_returns_key_on_class(DBTest):
    t = ArrayTest("entries", 0)
    with DBTest:
        assert ArrayTest.entries == t._page.entries
        assert ArrayTest.entries == ArrayTest._page.entries
        assert ArrayTest.entries == "e"


def test_size_returns_key_on_class(DBTest):
    t = ArrayTest("size", 0)
    with DBTest:
        assert ArrayTest.size == t._page.size
        assert ArrayTest.size == ArrayTest._page.size
        assert ArrayTest.size == "s"


def test_unset_page_count_queries_for_the_page_count(DBTest):
    t = ArrayTest("unset_page_count", 0)
    with DBTest:
        for i in range(6):
            t.append(i)
        t2 = ArrayTest("unset_page_count")
        t2.append(7)
        assert t.pages() == t2.page_count
        assert t2.page_count == 3
        assert t[2] == [7]


def test_all_returns_unmapped_entries(DBTest):
    t = ArrayTest("all_unmapped")
    with DBTest:
        for i in range(3):
            t.append({str(i): i})

        for o in t.all():
            assert isinstance(o, dict)


def test_iteration(DBTest):
    t = ArrayTest("iteration")
    with DBTest:
        items = set(range(15))
        for i in items:
            t.append(i)
        for page in t:
            if not page:
                break
            assert len(page) == 3
            for e in page:
                items.remove(e)
        assert items == set()


def test_array_regex_ignores_dots(DBTest):
    t = ArrayTest("with.dot")
    t2 = ArrayTest("with_dot")

    with DBTest:
        t.append(1)
        t2.append(2)

        assert t.all() == [1]
        assert t2.all() == [2]
