from copy import copy, deepcopy
from unittest import mock

from humbledb import Document
from humbledb.cursor import Cursor

from ..util import database_name


class DocTest(Document):
    config_database = database_name()
    config_collection = "test"

    user_name = "u"


def test_cloned_cursor_still_a_humbledb_cursor(DBTest):
    with DBTest:
        cursor = DocTest.find()
        cursor = cursor.clone()
        assert isinstance(cursor, Cursor)
        assert issubclass(cursor._doc_cls, DocTest)


def test_cloned_cursor_returns_correct_type(DBTest):
    with DBTest:
        # Ensure we have a document
        DocTest.insert({})
        # Get the cursor
        cursor = DocTest.find()
        assert isinstance(cursor[0], DocTest)
        # Check the clone
        cursor = cursor.clone()
        assert isinstance(cursor[0], DocTest)


def test_copy_of_cursor_returns_correct_type(DBTest):
    with DBTest:
        # Ensure we have a document
        DocTest.insert({})
        # Get the cursor
        cursor = DocTest.find()
        assert isinstance(cursor[0], DocTest)
        # Check the clone
        cursor = copy(cursor)
        assert isinstance(cursor[0], DocTest)


def test_deepcopy_of_cursor_returns_correct_type(DBTest):
    with DBTest:
        # Ensure we have a document
        DocTest.insert({})
        # Get the cursor
        cursor = DocTest.find()
        assert isinstance(cursor[0], DocTest)
        # Check the clone
        cursor = deepcopy(cursor)
        assert isinstance(cursor[0], DocTest)


def test_if_a_cursor_is_not_returned_properly_we_exit_quickly(DBTest):
    with DBTest:
        with mock.patch.object(DocTest, "collection") as coll:
            coll.find.__name__ = "find"
            cursor = DocTest.find()
            assert cursor is coll.find.return_value


def test_cursor_ensures_document_types_when_iterating_explicitly(DBTest):
    with DBTest:
        # Ensure we have a document
        DocTest.insert({})
        # Get the cursor
        cursor = DocTest.find()
        cursor = iter(cursor)
        item = cursor.next()
        assert isinstance(item, DocTest)


def test_cursor_ensures_document_types_when_iterating_to_list(DBTest):
    with DBTest:
        # Ensure we have a document
        DocTest.insert({})
        # Get the cursor
        cursor = DocTest.find()
        items = list(cursor)
        assert isinstance(items[0], DocTest)
