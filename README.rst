HumbleDB - MongoDB Object-Document Mapper
=========================================

HumbleDB is an extremely lightweight ODM that works with pymongo to provide a
convenient and easy to use interface. It enforces strict explictness when a
connection to a MongoDB cluster or replica set is being used, by disallowing
any read or write interaction outside of a context manager's context block.

.. image:: https://travis-ci.org/shakefu/humbledb.svg?branch=master
   :target: https://travis-ci.org/shakefu/humbledb

.. image:: https://coveralls.io/repos/shakefu/humbledb/badge.png?branch=master
   :target: https://coveralls.io/r/shakefu/humbledb?branch=master



Quick Example
-------------

.. code-block:: python

   >>> from humbledb import Mongo, Document
   >>> # config_database and config_collection are required attributes
   >>> class TestDoc(Document):
   ...     config_database = 'test'
   ...     config_collection = 'testdoc'
   ...     test_key = 't'
   ...     other_key = 'o'
   ...     
   >>> # When you create a Document instance, you can set its keys via any
   >>> # mapped attributes you create
   >>> doc = TestDoc()
   >>> doc.test_key = 'Hello'
   >>> doc.other_key = 'World'
   >>> # The __repr__ for the instance shows the actual doc
   >>> doc
   TestDoc({'t': 'Hello', 'o': 'World'})
   >>> # A Document instance is also a dict, but you have to access the key
   >>> # names directly
   >>> doc['o']
   u'World'
   >>> # Or use the mapped attribute
   >>> doc[TestDoc.test_key]
   u'Hello'
   >>> # The Mongo class manages database connection and is a context manager
   >>> with Mongo:
   ...     TestDoc.insert(doc)
   ...     
   >>> with Mongo:
   ...     found = TestDoc.find_one()
   ...     
   >>> found
   TestDoc({u'_id': ObjectId('50ad81586112797f89b99606'), u't': u'Hello', u'o': u'World'})
   >>> doc
   TestDoc({'_id': ObjectId('50ad81586112797f89b99606'), 't': 'Hello', 'o': 'World'})
   >>> found['_id']
   ObjectId('50ad81586112797f89b99606')
   >>> found['t']
   u'Hello'
   >>> found.test_key
   u'Hello'

See the documentation for more examples and detailed explanations.

Documentation
-------------

The complete documentation can be found on http://humbledb.readthedocs.org.

License
-------

See LICENSE.rst.

Contributors
------------

* `shakefu <https://github.com/shakefu>`_ (Creator, Maintainer)
* `paulnues <https://github.com/paulnues>`_

