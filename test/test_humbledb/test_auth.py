import mock
import pymongo
import pytool
import pyconfig

import humbledb
from ..util import *

from humbledb import Mongo, Document, Embed, _version


def teardown():
    DBTest.connection[database_name()].drop_collection('auth')


@raises(TypeError)
def test_invalid_mongo_credentials():
    class BadMongoCredentials(Mongo):
        config_host = 'localhost'
        config_auth = 'foo:bar:baz:'


def test_auth_call_with_no_config():
    class NoAuthMongo(Mongo):
        config_host = 'localhost'

    NoAuthMongo.authenticate(database_name())


def test_auth_logout():
    class AuthMongo(Mongo):
        config_host = 'localhost'
        config_auth = 'authuser:pass1'

    AuthMongo.authenticate(database_name())
    AuthMongo.logout(database_name())


def test_invalid_document_credentials():
    auth_check()
    class BadAuthDoc(Document):
        config_database = database_name()
        config_collection = 'auth'
        config_auth = '45:545:553:'

        value = 'v'

    bad_doc = BadAuthDoc()
    bad_doc.value = 'bar'

    try:
        with DBTest:
            BadAuthDoc.insert(bad_doc)
        raise RuntimeError('Failed to validate config_auth')
    except humbledb.errors.InvalidAuth:
        assert True


def test_document_retrieval_using_valid_document_credentials():
    auth_check()
    class AuthedDoc(Document):
        config_database = database_name()
        config_collection = 'auth'
        config_auth = 'authuser:pass1'

        user_name = 'u'

    new_doc = AuthedDoc()
    new_doc.user_name = 'foo'

    with DBTest:
        doc_id = AuthedDoc.insert(new_doc)
        queried_doc = AuthedDoc.find_one({AuthedDoc._id: doc_id})

    eq_(queried_doc, {'_id': doc_id, 'u': 'foo'})


def test_document_retrieval_using_invalid_document_credentials():
    auth_check()
    class AuthedDoc(Document):
        config_database = database_name()
        config_collection = 'auth'
        config_auth = 'foo:bar'

        user_name = 'u'

    new_doc = AuthedDoc()
    new_doc.user_name = 'foo'

    try:
        with DBTest:
            doc_id = AuthedDoc.insert(new_doc)
            queried_doc = AuthedDoc.find_one({AuthedDoc._id: doc_id})
        assert False
    except humbledb.errors.InvalidAuth:
        assert True


def test_document_retrieval_using_mongo_klass_credentials():
    auth_check()
    class AuthedDoc(Document):
        config_database = database_name()
        config_collection = 'auth'

        user_name = 'u'

    new_doc = AuthedDoc()
    new_doc.user_name = 'foo'

    with DBTest:
        doc_id = AuthedDoc.insert(new_doc)
        queried_doc = AuthedDoc.find_one({AuthedDoc._id: doc_id})

    eq_(queried_doc, {'_id': doc_id, 'u': 'foo'})


