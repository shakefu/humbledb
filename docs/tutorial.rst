.. highlight:: python
.. currentmodule:: humbledb.mongo

.. _PyPI: http://pypi.python.org/pypi/humbledb
.. _Pymongo: http://api.mongodb.org/python/current/
.. _Pytool: http://pypi.python.org/pypi/pytool
.. _Pyconfig: http://pypi.python.org/pypi/pyconfig
.. _github: http://github.com/shakefu/humbledb

========
Tutorial
========

This tutorial will introduce you to the concepts and features of the HumbleDB
micro-ODM and covers basic and advanced usage. It will teach you how to install
HumbleDB, how to create :class:`Document` and :class:`Mongo` subclasses that
fit your needs, and the HumbleDB way of manipulating documents. The :doc:`api`
covers more details, but has less explanation.

.. _installation:


Installation
============

HumbleDB requires Pymongo_ (``>=2.2.1``), Pytool_ (``>=1.1.0``) and
Pyconfig_. These are installed for you automatically when you install HumbleDB
via pip or easy_install.

.. code-block:: bash

   $ pip install -U humbledb   # preferred
   $ easy_install -U humbledb  # without pip


To get the latest and greatest development version of HumbleDB, clone the code
via github_ and install:

.. code-block:: bash

   $ git clone http://github.com/shakefu/humbledb.git
   $ cd humbledb
   $ python setup.py install


Quickstart: The humblest document
=================================

This tutorial assumes you already have HumbleDB :ref:`installed <installation>`
and working. Let's start with a very basic :class:`Document`::

   from humbledb import Document

   class HumbleDoc(Document):
       config_database = 'humble'
       config_collection = 'example'

       description = 'd'
       value = 'v'

The :attr:`~Document.config_database` and :attr:`~Document.config_collection`
attributes are required to tell the HumbleDoc class which database and
collection that it lives in.

HumbleDB's basic attribute access works by looking for class attributes whose
values are :py:class:`str` or :py:class:`unicode` objects, and mapping those
values to the attribute names given.

We see above that the ``description`` attribute is mapped to the ``'d'`` key,
and the ``value`` attribute is mapped to the ``'v'`` key. These keys can bet
set by assigning their attributes::

   doc = HumbleDoc()
   doc.description = "The humblest document"
   doc.value = 3.14

In addition to any keys you specify, every Document is given a ``_id``
attribute which maps to the ``'_id'`` key.

.. _keys-and-values:

.. rubric:: Accessing Keys and Values

When you access a mapped key on your document class, it returns the key for
you, so you can reference your short key names more readably::

   >>> HumbleDoc.description
   'd'
   >>> HumbleDoc.value
   'v'

When querying or setting keys you should use these attributes, rather than
the short key names, for more understandable code::

   HumbleDoc.find({HumbleDoc._id: 'example'})

   HumbleDoc.update({HumbleDoc._id: 'example'},
           {'$set': {HumbleDoc.value: 4}})

   HumbleDoc.find_one({HumbleDoc.value: 4})

When these same attributes are accessed on a document instance, they return
the current value of that key::

   >>> with Mongo:
   ...     doc = HumbleDoc.find_one()
   ...     
   >>> doc.description
   u'A humble example'
   >>> doc.value
   3.14159265358979

.. _connecting:

.. rubric:: Connecting to MongoDB

The :class:`Mongo` class is a context manager which takes care of establishing
a :py:class:`pymongo.connection.Connection` instance for you. By default, the
Mongo class will connect to ``'localhost'``, port ``27017`` (see
:ref:`subclassing-mongo` if you need different settings).

When doing any operation that hits the database, you always need to use the
:mod:`with <contextlib>` statement with :class:`Mongo` (or a
:ref:`subclass <subclassing-mongo>`)::

   with Mongo:
       HumbleDoc.insert(doc)
       docs = HumbleDoc.find({HumbleDoc.value: {'$gt': 3}})

The Mongo context ensures any operations you do are within a single request
(for consistency) and that the socket is released back to the connection pool
as soon as possible (for concurrency).

.. _collection-methods:

.. rubric:: Working with a Collection

For your convenience, all of the :py:class:`pymongo.collection.Collection`
methods are mapped onto your document class (but not onto class instances).
Because these methods imply using the MongoDB connection, they're only available
within a :class:`Mongo` context.

Within a :class:`Mongo` context, all the
:py:class:`~pymongo.collection.Collection` methods are available on your
document class::

   with Mongo:
       doc = HumbleDoc.find_one()

Without a context, a :py:exc:`RuntimeError` is raised::

   >>> HumbleDoc.insert
   Traceback (most recent call last):
      ...
   RuntimeError: 'collection' not available without context

:class:`Document` instances do not have collection methods and will raise a
:py:exc:`AttributeError`::

   >>> doc.insert
   Traceback (most recent call last):
      ...
   AttributeError: 'HumbleDoc' object has no attribute 'insert'

.. _documents:

Working with Documents
======================

Document subclasses provide a clean attribute oriented interface to your 
collection's documents, but at their heart, they're just dictionaries. The only
required attributes on a document are :attr:`~Document.config_database`, and
:attr:`~Document.config_collection`.

**Documents are dictionaries:**

::

   from humbledb import Document

   class Basic(Document):
       # These are required
       config_database = 'humble'
       config_collection = 'basic'

   # Documents are dictionaries
   doc = Basic()
   doc['my-key'] = 'Hello'

   # Documents can be initialized with dictionaries
   doc = Basic({'key': 'value'})
   doc['key'] == 'value'

.. _attribute-mapping:

Attribute Mapping
-----------------

Attributes are created by assigning string key in your class definition to
attribute names. These attributes are mapped to the dictionary keys internally.
In addition to any attributes you specify, a ``_id`` attribute is always
available.

Attributes names with a leading underscore (``_``) are not mapped to keys.

When an mapped attribute is accessed from the class, the short key is returned,
and when accessed from an instance, that instance's value for that key is
returned.

If a document doesn't have a value set for a mapped attribute, ``None`` is
returned (rather than raising an :exc:`AttributeError`), so you can easily
check whether an attribute exists.

When a document is inserted, its ``_id`` attribute is set to the created
:class:`~bson.objectid.ObjectId`, if it wasn't already set.

::

   class MyDoc(Document):
       config_database = 'humble'
       config_collection = 'mydoc'

       # Keys are mapped to attributes 
       my_attribute = 'my_key'

       # Private names are ignored
       _my_str = 'private'

   doc = MyDoc()

   # Unset attributes return None
   if not doc.my_attribute:
      # Attribute assignment works like normal
      doc.my_attribute = 'Hello'

   # Class attributes return the key
   MyDoc.my_attribute # 'my_key'

   # Instance attributes return the value
   doc.my_attribute # 'Hello'

   # Private names aren't mapped
   doc._my_str # 'private'

   doc._id # None

   if not doc._id:
      with Mongo:
         MyDoc.insert(doc)

   doc._id # ObjectId(...)


Embedded Documents
------------------

Attribute mapping to embedded documents is done via the :class:`Embed` class.
Because a document is also a dictionary, using Embed is totally optional, but
helps keep your code more readable.

An embedded document can be assigned mapped attributes, just like a document.

Mapped embedded document attributes that aren't assigned return an empty
dictionary when accessed.

When accessed via the class, an embedded document attribute returns the full
dot-notation key name. If you want just the key name of the attribute, it is
available as the attribute `key`.

Of course, embedded documents are nestable.

::

   from humbledb import Document, Embed

   class Example(Document):
       config_database = 'humble'
       config_collection = 'embed'

       # This maps embedded_doc to embed_key
       embedded_doc = Embed('embed_key')

       # This maps embedded_doc.my_attribute to embed_key.my_key
       embedded_doc.my_attribute = 'my_key'

       # This is a nested embedded document
       embedded_doc.nested_doc = Embed('nested_key')
       embedded_doc.nested_doc.value = 'val'


   empty_doc = Example()

   # Empty or missing embedded documents are returned as an empty dictionary
   empty_doc.embedded_doc # {}

   # Missing attributes are returned as None
   empty_doc.embedded_doc.my_attribute # None

   doc = Example()

   # Attribute assignment works like normal
   if not doc.embedded_doc:
      doc.embedded_doc.my_attribute = "A Fish"

   doc.embedded_doc.nested_doc.value = 42

   # Class attributes return the dot-notation key
   Example.embedded_doc                  # 'embed_key'
   Example.embedded_doc.my_attribute     # 'embed_key.my_key'
   Example.embedded_doc.nested_doc       # 'embed_key.nested_key'
   Example.embedded_doc.nested_doc.value # 'embed_key.nested_key.val'

   # The subdocument key is available via .key
   Example.embedded_doc.my_attribute.key     # 'my_key'
   Example.embedded_doc.nested_doc.key       # 'nested_key'
   Example.embedded_Doc.nested_doc.value.key # 'val'

   # Instances return the value
   doc.embedded_doc.my_attribute     # "A Fish"
   doc.embedded_doc.nested_doc.value # 42
   doc.embedded_doc.nested_doc       # {'nested_key': {'val': 42}}
   doc.embedded_doc                  # {'embed_key': {'my_key': "A Fish", 
                                     #     'nested_key': {'val: 42}}}


Specifying Indexes
==================

TODO

.. _subclassing-mongo:

Configuring Connections
=======================

TODO

