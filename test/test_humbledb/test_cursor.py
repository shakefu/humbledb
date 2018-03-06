from copy import copy, deepcopy

import mock

from ..util import *
from humbledb import Document
from humbledb.cursor import Cursor


def teardown():
    DBTest.connection.drop_database(database_name())


class DocTest(Document):
    config_database = database_name()
    config_collection = 'test'

    user_name = 'u'


def test_cloned_cursor_still_a_humbledb_cursor():
    with DBTest:
        cursor = DocTest.find()
        cursor = cursor.clone()
        is_instance_(cursor, Cursor)
        is_subclass_(cursor._doc_cls, DocTest)


def test_cloned_cursor_returns_correct_type():
    with DBTest:
        # Ensure we have a document
        DocTest.insert({})
        # Get the cursor
        cursor = DocTest.find()
        is_instance_(cursor[0], DocTest)
        # Check the clone
        cursor = cursor.clone()
        is_instance_(cursor[0], DocTest)


def test_copy_of_cursor_returns_correct_type():
    with DBTest:
        # Ensure we have a document
        DocTest.insert({})
        # Get the cursor
        cursor = DocTest.find()
        is_instance_(cursor[0], DocTest)
        # Check the clone
        cursor = copy(cursor)
        is_instance_(cursor[0], DocTest)


def test_deepcopy_of_cursor_returns_correct_type():
    with DBTest:
        # Ensure we have a document
        DocTest.insert({})
        # Get the cursor
        cursor = DocTest.find()
        is_instance_(cursor[0], DocTest)
        # Check the clone
        cursor = deepcopy(cursor)
        is_instance_(cursor[0], DocTest)


def test_if_a_cursor_is_not_returned_properly_we_exit_quickly():
    with DBTest:
        with mock.patch.object(DocTest, 'collection') as coll:
            coll.find.__name__ = 'find'
            cursor = DocTest.find()
            is_(cursor, coll.find.return_value)


def test_cursor_ensures_document_types_when_iterating_explicitly():
    with DBTest:
        # Ensure we have a document
        DocTest.insert({})
        # Get the cursor
        cursor = DocTest.find()
        cursor = iter(cursor)
        item = cursor.next()
        is_instance_(item, DocTest)


def test_cursor_ensures_document_types_when_iterating_to_list():
    with DBTest:
        # Ensure we have a document
        DocTest.insert({})
        # Get the cursor
        cursor = DocTest.find()
        items = list(cursor)
        is_instance_(items[0], DocTest)

