HumbleDB - MongoDB Object-Document Mapper
=========================================

HumbleDB is an extremely lightweight ODB that works with pymongo to provide a
convenient and easy to use interface. It enforces strict explictness when a
connection to a MongoDB cluster or replica set is being used, by disallowing
any read or write interaction outside of a context manager's context block.

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

The two main parts to HumbleDB are the `Document` class and the `Mongo` class.

The `Document` class
--------------------

HumbleDB Document classes are subclasses of dicts, which mean they play quite
nicely with the underly pymongo interface. An individual Document subclass
works both as a document instance and as an interface to that document's
collection.

The Document superclass provides some nice conveniences for its subclasses:

#. You can map short key names, to long, human readable attributes, for easy
   access and better understandability in code.
#. All of the `pymongo.Collection
   <http://api.mongodb.org/python/current/api/pymongo/collection.html>`_
   methods are mapped onto the Document subclass for easy access.
#. All documents returned by query operations are converted into instances of
   your subclass.

The `Mongo` class
-----------------

The `Mongo` class is a superclass designed to hold a long-lived
`pymongo.Connection
<http://api.mongodb.org/python/current/api/pymongo/connection.html>`_ instance.
Since pymongo 2.2, pymongo has had the ability to support greenlets and
concurrent access via socket pools, and the `Mongo` superclass is designed with
this in mind. It primarily acts as a context manager, allowing you to minimize
the amount of time that a greenlet or thread holds a socket out of the socket
pool. In its most basic functioning, this context manager behavior is a wrapper
around `Connection.start_request()
<http://api.mongodb.org/python/current/api/pymongo/connection.html#pymongo.connection.Connection.start_request>`_.

Here is a basic example of a `Mongo` subclass:

.. code-block:: python

   from humbledb import Mongo

   class MyCluster(Mongo):
      config_host = 'mongo.example.org'
      config_port = 30001

The `Mongo` class can be used directly, without subclassing, if all you need is
access to the default host and port (``localhost`` and ``27017``). In
production environments, where multiple database clusters are often in use,
subclassing lets you be explicit in which cluster you're connecting to.
Subclassing also allows you to connect to named replica sets:

.. code-block:: python

   from humbledb import Mongo

   class MyReplicaSet(Mongo):
      config_host = 'replica.example.org'
      config_port = 30002
      config_replica = 'ReplicaSetName'


