HumbleDB - MongoDB Object-Document Mapper
=========================================

HumbleDB is an extremely lightweight ODB that works with pymongo to provide a
convenient and easy to use interface.

The two main parts to HumbleDB are the `Document` class, and the `Mongo` class.

The `Mongo` class
------------------------

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

Here is a basic example of a `Mongo` subclass::

   from humbledb import Mongo

   class MyCluster(Mongo):
      config_host = 'mongo.example.org'
      config_port = 30001

The `Mongo` class can be used directly, without subclassing, if all you need is
access to the default host and port (``localhost`` and ``27017``). In
production environments, where multiple database clusters are often in use,
subclassing lets you be explicit in which cluster you're connecting to.
Subclassing also allows you to connect to named replica sets::

   from humbledb import Mongo

   class MyReplicaSet(Mongo):
      config_host = 'replica.example.org'
      config_port = 30002
      config_replica = 'ReplicaSetName'


