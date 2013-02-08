.. highlight:: python

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
HumbleDB, how to create :class:`~humbledb.document.Document` and
:class:`~humbedb.mongo.Mongo` subclasses that fit your needs, and the HumbleDB
way of manipulating documents. The :doc:`api` covers more details, but has less
explanation.

.. _installation:


Installation
============

HumbleDB requires Pymongo_ (``>=2.0.1``), Pytool_ (``>=1.1.0``) and
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

The :class:`~humbledb.mongo.Mongo` class is a context manager which takes care
of establishing a :py:class:`pymongo.connection.Connection` instance for you.
By default, the Mongo class will connect to ``'localhost'``, port ``27017``
(see :ref:`subclassing-mongo` if you need different settings).

When doing any operation that hits the database, you always need to use the
:mod:`with <contextlib>` statement with :class:`~humbledb.mongo.Mongo` (or a
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
within a :class:`~humbledb.mongo.Mongo` context.

Within a :class:`~humbledb.mongo.Mongo` context, all the
:py:class:`~pymongo.collection.Collection` methods are available on your
document class::

   with Mongo:
       doc = HumbleDoc.find_one()

Without a context, a :py:exc:`RuntimeError` is raised::

   >>> HumbleDoc.insert
   Traceback (most recent call last):
      ...
   RuntimeError: 'collection' not available without context

:class:`~humbledb.document.Document` instances do not have collection methods
and will raise a :py:exc:`AttributeError`::

   >>> doc.insert
   Traceback (most recent call last):
      ...
   AttributeError: 'HumbleDoc' object has no attribute 'insert'

.. _documents:

Working with Documents
======================

Document subclasses provide a clean attribute oriented interface to your 
collection's documents, but at their heart, they're just dictionaries. The only
required attributes on a document are
:attr:`~humbledb.document.Document.config_database`, and
:attr:`~humbledb.document.Document.config_collection`.

.. rubric:: Example: Documents are dictionaries

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

If a document doesn't have a value set for a mapped attribute, ``{}`` is
returned (rather than raising an :exc:`AttributeError`), so you can easily
check whether an attribute exists. This also allows you to create embedded
documents whose keys are not mapped.

When a document is inserted, its ``_id`` attribute is set to the created
:class:`~bson.objectid.ObjectId`, if it wasn't already set.

.. versionchanged:: 3.0
   Unset attributes on a Document return ``{}`` rather than ``None``

.. rubric:: Example: Attribute mapping

.. code-block:: python
   :emphasize-lines: 6

   class MyDoc(Document):
       config_database = 'humble'
       config_collection = 'mydoc'

       # Keys are mapped to attributes 
       my_attribute = 'my_key'

       # Private names are ignored
       _my_str = 'private'

       # Non string values are ignored
       an_int = 1

   doc = MyDoc()

   # Unset attributes return {}, which evaluates to False
   if not doc.my_attribute:
      # Attribute assignment works like normal
      doc.my_attribute = 'Hello'
      # Attribute deletion works like normal too
      del doc.my_attribute

   # You can explicitly check if you expect to assign values which also 
   # evaluate to False
   if doc.my_attribute == {}:
      doc.my_attribute = 'Hello World'

   # Class attributes return the key
   MyDoc.my_attribute # 'my_key'

   # Instance attributes return the value
   doc.my_attribute # 'Hello World'

   # Private names aren't mapped
   doc._my_str # 'private'

   # Neither are non-string values
   doc.an_int # 1

   doc._id # {}

   if not doc._id:
      with Mongo:
         MyDoc.insert(doc)

   doc._id # ObjectId(...)


Introspecting Documents
-----------------------

Sometimes it's useful to be able to introspect a document schema to find out
what attributes or keys are mapped. To do this, HumbleDB provides two methods,
:meth:`~humbledb.document.Document.mapped_keys` and
:meth:`~humbledb.document.Document.mapped_attributes`. These methods will
return all the mapped dictionary keys and document attributes, respectively,
excluding the ``_id`` key/attribute.

.. rubric:: Example: Introspecting documents

::

   class MyDoc(Document):
       config_database = 'humble'
       config_collection = 'mydoc'

       my_attr = 'k'
       other_attr = 'o'

   MyDoc.mapped_keys() # ['k', 'o']
   MyDoc.mapped_attributes() # ['my_attr', 'other_attr']

   # Mapping an arbitrary dict, while restricting keys
   some_dict = {'spam': 'ham', 'k': True, 'o': "Hello"}

   # Create an empty doc
   doc = MyDoc()

   # Iterate over the mapped keys, assigning common keys
   for key in MyDoc.mapped_keys():
       if key in some_dict:
           doc[key] = some_dict[key]

.. _embedding-documents:

Embedding Documents
===================

Attribute mapping to embedded documents is done via the :class:`Embed` class.
Because a document is also a dictionary, using Embed is totally optional, but
helps keep your code more readable.

An embedded document can be assigned mapped attributes, just like a document.

Mapped embedded document attributes that aren't assigned return an empty
dictionary when accessed.

When accessed via the class, an embedded document attribute returns the full
dot-notation key name. If you want just the key name of the attribute, it is
available as the attribute `key`.

.. rubric:: Example: Embedded documents and nested documents

::

   from humbledb import Document, Embed

   class Example(Document):
       config_database = 'humble'
       config_collection = 'embed'

       # Any mapped attribute can be used as an embedded document
       my_attribute = 'my_attr'

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

   # Missing attributes are returned as {} so you can have unmapped subdocs
   empty_doc.embedded_doc.my_attribute # {}

   doc = Example()

   # You can use attributes as unmapped embedded documents
   doc.my_attribute['embedded_key'] = 'Hello'
   doc.my_attribute # {'embedded_key': 'Hello'}
   doc # {'my_attr': {'embedded_key': 'Hello'}}

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

.. rubric:: Example: A BlogPost class with embedded document

.. code-block:: python
   :emphasize-lines: 7

   from humbledb import Document, Embed

   class BlogPost(Document):
       config_database = 'humble'
       config_collection = 'posts'

       meta = Embed('m')
       meta.timestamp = 'ts'
       meta.author = 'a'
       meta.tags = 't'

       title = 't'
       preview = 'p'
       content = 'c'

As you can see using embedded documents here lets you keep your keys short, and
your code clear and understandable.

Querying, Updating and Deleting
===============================

TODO

All the standard pymongo find/update/remove, etc., are mapped onto Document
subclasses.

.. _specifying-indexes:

Specifying Indexes
==================

Indexes are specified using the
:attr:`~humbledb.document.Document.config_indexes` attribute.  This attribute
should be a list of attribute names to index. These names will be automatically
mapped to their key names when the index call is made.  More complicated
indexes with different sort ordering, uniqueness, or sparseness currently can't
be created with HumbleDB's ``config_indexes``. This will change soon.

HumbleDB uses an :meth:`~pymongo.collection.Collection.ensure_index` call with
a TTL of 24 hours, and ``background=True``. This will be called before any
:meth:`~pymongo.collection.Collection.find`, 
:meth:`~pymongo.collection.Collection.find_one`, or
:meth:`~pymongo.collection.Collection.find_and_modify` operation.

.. rubric:: Example: Indexes on a BlogPost class

.. code-block:: python
   :emphasize-lines: 4

   class BlogPost(Document):
      config_database = 'humble'
      config_collection = 'posts'
      config_indexes = ['author', 'timestamp', 'tags']

      timestamp = 'ts'
      author = 'a'
      tags = 'g'
      title = 't'
      content = 'c'

.. _subclassing-mongo:

Configuring Connections
=======================

The :class:`~humbledb.mongo.Mongo` class provides a default connection for you,
but what do you do if you need to connect to a different host, port, or a
replica set? You can subclass Mongo to change your settings to whatever you
need. 

Mongo subclasses are used as context managers, just like Mongo. Different
Mongo subclasses can be nested within one another, should your code require it,
however you cannot nest a connection within itself (this will raise a
``RuntimeError``).

.. rubric:: Connection Settings

* **config_host** (``str``) - Hostname to connect to.
* **config_port** (``int``) - Port to connect to.
* **config_replica** (``str``, optional) - Name of the replica set.

If ``config_replica`` is present on the class, then HumbleDB will automatically
use a :class:`~pymongo.connection.ReplicaSetConnection` for you. (Requires 
``pymongo >= 2.1``.)

.. rubric:: Global Connection Settings

These settings are available globally through Pyconfig_ configuration keys. Use
either :func:`Pyconfig.set` (i.e. ``pyconfig.set('humbledb.connection_pool',
20)`` or create a Pyconfig_ plugin to change these.

* **humbledb.connection_pool** (``int``, default: ``10``) - Size of the
  connection pool to use.
* **humbledb.allow_explicit_request** (``bool``, default: ``False``) - Whether
  or not :meth:`~humbledb.mongo.Mongo.start` can be used to define a request,
  without using Mongo as a context manager.
* **humbledb.auto_start_request** (``bool``, default: ``True``) - Whether to
  use ``auto_start_request`` with the :class:`~pymongo.connection.Connection`
  instance.
* **humbledb.use_greenlets** (``bool``, default: ``False``) - Whether to use
  ``use_greenlets`` with the :class:`~pymongo.connection.Connection`
  instance. (This is only needed if you intend on using threading and greenlets
  at the same time.)

More configuration settings are going to be added in the near future, so you
can customize your :class:`~pymongo.connection.Connection` to completely suit
your needs.

.. rubric:: Example: Using different connection settings

.. code-block:: python

   from humbledb import Mongo

   # A basic class which connects to a different host and port
   class MyDB(Mongo):
       config_host = 'mydb.example.com'
       config_port = 3001

   # A replica set class which will use a ReplicaSetConnection
   class MyReplica(Mongo):
       config_host = 'replica.example.com'
       config_port = 3002
       config_replica = 'RS1'

   # Use your custom subclasses as context managers
   with MyDB:
       docs = MyDoc.find({MyDoc.value {'$gt': 3}})

   # You can nest different connections when you need to
   # (But you cannot nest the same connection)
   with MyReplica:
       values = MyGroup.find({MyGroup.tags: 'example'})
       value = sum(doc['value'] for doc in values)

       # HumbleDB allows you to nest different connections when you need
       # consistency
       with MyDoc:
           doc = MyDoc()
           doc.value = value
           MyDoc.insert(doc)

       MyGroup.update({MyGroup.tags: 'example'},
               {'$push': {MyGroup.related: MyDoc._id},
               multi=True)




