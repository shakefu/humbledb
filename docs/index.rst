.. HumbleDB documentation

.. highlight:: python
.. currentmodule:: humbledb.mongo

.. _Pymongo: http://api.mongodb.org/python/current/
.. _MongoDB: http://www.mongodb.org/
.. _PyPI: http://pypi.python.org/pypi/humbledb
.. _Pytool: http://pypi.python.org/pypi/pytool
.. _Pyconfig: http://pypi.python.org/pypi/pyconfig
.. _github: http://github.com/shakefu/humbledb
.. _MongoEngine: http://mongoengine.org/
.. _MongoAlchemy: http://www.mongoalchemy.org/
.. _MiniMongo: https://github.com/slacy/minimongo


===========================
HumbleDB: MongoDB micro-ODM
===========================

HumbleDB is a thin wrapper around Pymongo_ for MongoDB_ that is designed to
make working with flexible schema documents easy and readable.  

* **Readable:** Short document keys can be mapped to long attribute
  names to keep document size small and efficient, while providing completely
  readble code.
* **Flexible:** A :class:`Document` is also a dictionary, so you have
  maximum flexibility in your schema - there are no restricitons.
* **Concurrent:** HumbleDB is thread-safe and greenlet-safe and provides a
  connection paradigm which minimizes the amount of time a socket is used from
  the connection pool.

.. rubric:: Why HumbleDB?

With so many excellent MongoDB Python ORMs, ODMs, and interfaces out there such
as MongoEngine_, MongoAlchemy_, MiniMongo_, and of course Pymongo_ itself, why
would I write yet another one? The answer is, as usual, that those excellent
software projects didn't do exactly what I want. I enjoy that Python and
MongoDB are both completely flexible in their ability to be modified on the
fly, and be adapted very easily to unique problems. I feel like Python and
MongoDB are almost mirrors of each other in that way - a perfect pair. After
all, at their heart, both Python and MongoDB objects are just dictionaries.

But there's a problem with MongoDB, which is that keys are repeated in every
document. When you create a MongoDB schema that's verbose, readable, and easily
understandable, you end up with key names that take up more space than the data
you're trying to store! When you use short, single character or double
character key names, you save lots of space, but your schema becomes almost
completely unintelligible.

Of course, MongoEngine and MongoAlchemy let you map your attributes to
different or shorter key names, but they also are heavy - instantiating a large
number of ORM objects can be 10x or 100x slower than doing the same query with
Pymongo.

This is the problem that HumbleDB tries to solve - it provides a clean,
readable interface for the shortest keys you can use, saving your database RAM
for more documents, using resources more efficently, and exposing all the
power and flexibility of Pymongo underneath. It's called "Humble" because
"humble" is another word for "small", which is what it tries to be.

.. rubric:: Example: The humblest document

::

   >>> from humbledb import Mongo, Document
   >>> class HumbleDoc(Document):
   ...     # config_database and config_collection are required configuration
   ...     # for every Document subclass
   ...     config_database = 'humble'
   ...     config_collection = 'examples'
   ...     # The 'd' document key is mapped to the description attribute
   ...     description = 'd'
   ...     # Same for the 'v' key and the value attribute
   ...     value = 'v'
   ...     
   >>> # Create a new empty document
   >>> doc = HumbleDoc()
   >>> # Set some values in the document
   >>> doc.description = "A humble example"
   >>> doc.value = 3.14159265358979
   >>> # with Mongo: tells HumbleDoc to use the default MongoDB connection
   >>> with Mongo:
   ...     # The insert method (and others) are the same as the pymongo methods
   ...     HumbleDoc.insert(doc)
   ...     
   >>> # Newly created documents will have their _id field set, and you can see
   >>> # what the raw document would look like in MongoDB
   >>> doc
   HumbleDoc({'_id': ObjectId('50c3e72c6112798c3bcde02d'),
      'd': 'A humble example', 'v': 3.14159265358979})

.. rubric:: What's going on here?

* ``config_database = 'humble'`` - This tells the document that it's stored 
  in the ``'humble'`` database.
* ``config_collection = 'examples'`` - This tells the document that it's part
  of the ``'examples'`` collection.
* ``description = 'd'`` - This maps the ``description`` attribute to the
  document key ``'d'`` (see :ref:`attribute-mapping`).
* ``value = 'v'`` - This maps the ``value`` attribute to the document key
  ``'v'``.
* ``with Mongo:`` - This :class:`Mongo` context manager tells the
  document which MongoDB connection to use (see :ref:`Connecting to MongoDB
  <connecting>`). 
* ``HumbleDoc.insert(doc)`` - This inserts ``doc`` into the HumbleDoc
  collection (see :ref:`Working with a Collection <collection-methods>`).

.. rubric:: Download and Install

Install the latest stable release via PyPI_ (``pip install -U humbledb``).
HumbleDB requires Pymongo_ (``>=2.2.1``), Pytool_ (``>=1.1.0``) and
Pyconfig_, and runs on Python 2.7 or newer (though maybe not 3.x).

The code for HumbleDB can be found on github_.


User's Guide
============

.. toctree::
   :maxdepth: 2

   tutorial
   api

.. include:: ../LICENSE.rst
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

