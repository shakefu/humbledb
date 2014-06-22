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

HumbleDB requires Pymongo_ (``>=2.0.1``), Pytool_ (``>=3.0.1``) and
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
Because these methods imply using the MongoDB connection, they're only
available within a :class:`~humbledb.mongo.Mongo` context.

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

   # You also can query using arbitrary keys
   with Mongo:
      docs = Basic.find({'my-key': {'$exists': True}})

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

.. _default-values:

Giving Documents Default Values
-------------------------------

Sometimes it's useful to allow a document to provide a default value for a
missing key. HumbleDB provides a convenient syntax for specifying both
persisted and unpersisted default values.

.. versionadded:: 5.2.0

Both persisted and unpersisted values are declared by assigning a 2-tuple to an
attribute where the first item is a string document key, and the second item is
a default value.

If the second item is a callable, then that indicates that the value
should be persisted. It will be called once on first access or first save and
persisted with the document.

By convention, HumbleDB uses the no-parentheses form of tuple
declaration when declaring default values.

Lastly, when serializing to JSON via the
:meth:`~humbledb.document.Document.for_json` method, the default values will be
inserted into the resulting JSON.

* ``attr = 'key', value`` - If ``value`` is not callable, provide an
  unpersisted default value, which is available through attribute access only,
  and not part of the document.

  **Examples**:

  .. code-block:: python
     :emphasize-lines: 7

      class MyDoc(Document):
          config_database = 'humble'
          config_collection = 'docs'

          attr = 'a'  # Regular mapping

          # Any non-callable as the second item is used as a default value
          truth = 't', False
          number = 'u', 1
          name = 'n', "humble"

          # Any expression may be used to declare an unpersisted default
          some_value = 'v', func()  # Where func() returns a non-callable
          one_day = 'd', 60*60*24

* ``attr = 'key', default`` - Where ``default`` is a callable, provide a
  persisted default value, which will become part of the document the first
  time it's accessed via attribute or inserted or saved. Updates do not trigger
  default values.

  **Examples**:

  .. code-block:: python
     :emphasize-lines: 12,17,21

      class MyDoc(Document):
          config_database = 'humble'
          config_collection = 'docs'

          attr = 'a'  # Regular mapping

          # A callable makes this a persisted default - as soon as it's
          # accessed, it is assigned to the doc, or when saved or inserted

          # Here, my_func() will be called without arguments to provide a
          # default value which will be saved with the document
          my_value = 'v', my_func

          # Here, uuid.uuid4() will be called - note the lack of parens, we're
          # not calling it (which would return a value) - we're providing the
          # function itself
          uid = 'u', uuid.uuid4

          # Here, the datetime.now() function will be called on save which is
          # a convenient way to provide a creation timestamp
          created = 'c', datetime.now

.. rubric:: Example: Declaring default values for keys

::

   class BlogPost(Document):
       config_database = 'humble'
       config_collection = 'posts'

       title = 't'  # Normal attribute
       author = 'a'  # Still normal

       public = 'p', False  # Default value that is not saved automatically

       created = 'c', datetime.now  # This will be saved to the document


   # Create a post
   post = BlogPost()
   post.title = "A post"
   post.author = "HumbleDB"

   # The default value is provided on the document object when accessed via an
   # attribute
   post.public  # False

   # But it isn't part of the document itself, so dict key access will raise a
   # KeyError
   post[BlogPost.public]  # KeyError
   post['p']  # KeyError

   # After the first access, the persisted default is called and the returned
   # value is stored in the document and will be consistent from then on
   post.created  # datetime(2014, 2, 14, 6, 59, 0)

   # Saving the post would also call the persisted default and store the value

   # Save the post and reload it
   with Mongo:
       _id = BlogPost.save(post)
       post = BlogPost.find_one(_id)

   # The unpersisted default value is not stored with the document
   post  # BlogPost({'_id': ObjectId(), 't': "A post", 'a': "HumbleDB",
         #         'c': datetime(2014, 2, 14, 6, 59, 0)})

   # But it's still available on the document object
   post.public  # False

   # Once modified, the value will be saved and retrieved like normal
   post.public = True
   with Mongo:
       BlogPost.save(post)

   post  #  BlogPost({'_id': ObjectId(), 't': "A post", 'a': "HumbleDB",
         #         'p': True, 'c': datetime(2014, 2, 14, 6, 59, 0)})


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

.. _overriding-authentication:

Overriding Authentication
-------------------------

Because each document is assigned to a specific database using the
`config_database` attribute, you may have the situation where a database
has its own specific credentials.  In this case, you may override the
credentials of the :class:`~humbledb.mongo.Mongo` class by giving
the document its own credentials using the `config_auth` attribute.

.. rubric:: Example: Setting up a document with specific
    authentication parameters

::

   class AuthedDoc(Document):
       config_database = 'authed_humble'
       config_collection = 'authdoc'
       config_auth = 'anotheruser:supersecret'

       value = 'v'

    with AuthedDB:
       some_doc = AuthedDoc.find({AuthedDoc.value: 'foo'})

.. versionadded:: 5.2.0

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

Embedded Document Lists
-----------------------

Sometimes your documents will have list of embedded documents in them, and for
your convenience, HumbleDB allows you to use attribute mapping on those
documents as well. Because attribute mapping is not just useful for retrieval,
but also for creation, HumbleDB provides a special :meth:`new` method for
creating new embedded documents within lists.

HumbleDB doesn't treat embedded lists specially unless they actually have a
list value. This is because HumbleDB's philosophy is to not validate data
types based on their keys, just like MongoDB's.

You can also embed lists within documents within lists, etc., to your heart's
delight and mapped attributes will work as you would expect.

.. rubric:: Creating embedded documents within a list

The easiest way to create embedded documents within a list is to use the
:meth:`new` helper. Of course, you can always do it "manually" by building and
appending dictionaries, but who wants to do that?

.. code-block:: python
   :emphasize-lines: 6-7,14-15,19

   # An example student roster
   class Roster(Document):
       config_database = 'humble'
       config_collection = 'lists'

       # Embedded lists are declared the same way as embedded documents
       students = Embed('s')
       students.name = 'n'
       students.grade = 'g'

   # Create a new roster instance
   roster = Roster()

   # You must assign a list to it first
   roster.students = []

   # You can use the new() convenience method which creates and appends an
   # empty embedded document to your list
   student = roster.students.new()
   student.name = "Lisa Simpson"
   student.grade = "A"

   # Note: We don't have to add it to our list - it is already appended
   # roster.students.append(student) # DON'T DO THIS: it will create duplicates

   # Everything else works the same
   with Mongo:
      Roster.insert(roster)

.. rubric:: Retrieving embedded list data

Upon retrieval, HumbleDB knows if an :class:`~humbledb.document.Embed`
attribute has a list assigned to it, and lets you use your mapped attributes
normally.

.. code-block:: python
   :emphasize-lines: 6,8,11

   # Contining our example from above
   with Mongo:
      roster = Roster.find_one()

   # You can iterate over it like any list
   for student in roster.students:
      # You get attributes mapped to your embedded document values
      print student.name, student.grade

      # You can modify attributes of the embedded list items
      student.grade = "A" # Everybody gets As!

   # Once modified, you can save your changes
   with Mongo:
      Roster.save(roster)

.. rubric:: Querying within lists

Because HumbleDB gives you dot-notation keys for embedded attribute mappings,
querying for list values is straight-forward.

.. code-block:: python

   # Find a roster containing a given student
   with Mongo:
      roster = Roster.find_one({Roster.students.name: "Bart Simpson"})

   # Find all rosters where at least one student has an F
   with Mongo:
      rosters = Roster.find({Roster.students.grade: "F"})

Querying, Updating and Deleting
===============================

.. currentmodule:: humbledb.mongo

All the standard pymongo find/update/remove, etc., are mapped onto Document
subclasses, however these are only available within a :class:`Mongo` context.
If you attempt to access the :attr:`~humbledb.document.Document.collection`
attribute of a document outside a :class:`Mongo` context, a :exc:`RuntimeError`
will be raised.

.. rubric:: Document methods

.. currentmodule:: humbledb.document

For your convenience, all the methods of the :attr:`Document.collection` are
mapped onto the document class.

Here's a listing of all those methods as of :py:mod:`pymongo` 2.4:

======================================================  ===============================================================  =================================================================
:py:meth:`~pymongo.collection.Collection.aggregate`     :py:meth:`~pymongo.collection.Collection.find_and_modify`        :py:meth:`~pymongo.collection.Collection.options`
:py:meth:`~pymongo.collection.Collection.count`         :py:meth:`~pymongo.collection.Collection.find_one`               :py:meth:`~pymongo.collection.Collection.reindex`
:py:meth:`~pymongo.collection.Collection.create_index`  :py:meth:`~pymongo.collection.Collection.get_lasterror_options`  :py:meth:`~pymongo.collection.Collection.remove`
:py:meth:`~pymongo.collection.Collection.distinct`      :py:meth:`~pymongo.collection.Collection.group`                  :py:meth:`~pymongo.collection.Collection.rename`
:py:meth:`~pymongo.collection.Collection.drop`          :py:meth:`~pymongo.collection.Collection.index_information`      :py:meth:`~pymongo.collection.Collection.save`
:py:meth:`~pymongo.collection.Collection.drop_index`    :py:meth:`~pymongo.collection.Collection.inline_map_reduce`      :py:meth:`~pymongo.collection.Collection.set_lasterror_options`
:py:meth:`~pymongo.collection.Collection.drop_indexes`  :py:meth:`~pymongo.collection.Collection.insert`                 :py:meth:`~pymongo.collection.Collection.unset_lasterror_options`
:py:meth:`~pymongo.collection.Collection.ensure_index`  :py:meth:`~pymongo.collection.Collection.map_reduce`             :py:meth:`~pymongo.collection.Collection.update`
:py:meth:`~pymongo.collection.Collection.find`
======================================================  ===============================================================  =================================================================

.. rubric:: Example: A blog post document

This class is used for all the examples in this section.

.. code-block:: python

   # A basic blog post class for illustration
   class BlogPost(Document):
      config_database = 'humble'
      config_collection = 'posts'
      config_indexes = [Index('meta.url', unique=True)]

      meta = Embed('m')
      meta.tags = 't'
      meta.published = 'p'
      meta.url = 's'

      author = 'a'
      title = 't'
      body = 'b'

.. rubric:: Best practices

Reference keys via their attributes when building query, update, or removal
dictionaries. For example, use ``BlogPost.meta.tags`` rather than ``'m.t'``.
This helps keep your code clean, readable, and avoids typos in string keys.

.. code-block:: python
   :emphasize-lines: 1,6

   # GOOD
   # Clear, typo-proof and highly readlable
   with Mongo:
      BlogPost.find({BlogPost.author: 'Humble'}).sort(BlogPost.meta.published)

   # BAD
   # Hard to read, prone to typos, and obfuscated
   with Mongo:
      BlogPost.find({'a': 'Humble'}).sort('m.p')


.. rubric:: Creating, inserting, and updating documents

If you're familiar with how Pymongo does inserting and updating, using HumbleDB
will be much the same. The main difference is that HumbleDB lets you use
attributes to reference the document keys, rather than using string keys.

.. code-block:: python

   # Creating a new post
   post = BlogPost()
   post.meta.tags = ['python', 'humbledb']
   post.meta.url = 'using-humbledb'
   post.author = "Humble"
   post.title = "How to Use HumbleDB"
   post.body = "Lorem ipsum, etc."

   # Inserting a new post
   with Mongo:
      post_id = BlogPost.insert(post)

   # Updating a post atomically
   with Mongo:
      BlogPost.update({BlogPost._id: post_id},
         {'$set': {BlogPost.meta.published: datetime.now()}})

   # Updating a post by retrieval
   with Mongo:
      post = BlogPost.find_one({BlogPost.meta.url: 'using-humbledb'})
      post.meta.published = False
      BlogPost.save(post)

.. rubric:: Querying for documents

Querying, like inserting and updating, works just like raw Pymongo, but with
the convenience and readability of using attributes instead of string keys.

.. code-block:: python

   # Get all posts by an author
   with Mongo:
      posts = BlogPost.find({BlogPost.author: "Humble"})

   # Get 10 most recent posts by an author
   with Mongo:
      posts = BlogPost.find({BlogPost.author: "Humble"})
      posts = posts.sort(BlogPost.meta.published, humbledb.DESC)
      posts = posts.limit(10)

   # Get all unpublished posts
   with Mongo:
      posts = BlogPost.find({BlogPost.meta.published: {'$exists': False}})

   # Get an individual post according to its URL
   with Mongo:
      post = BlogPost.find_one({BlogPost.meta.url: 'using-humbledb'})

   # Unpublish a post and retrieve it
   with Mongo:
      post = BlogPost.find_and_modify({BlogPost.meta.url: 'using-humbledb'},
            {'$unset': {BlogPost.meta.published: 1}}, new=True)

   # Find all posts with a Python tag
   with Mongo:
      posts = BlogPost.find({BlogPost.meta.tags: 'python'})

.. rubric:: Removing documents

Removing works just like removing in Pymongo, but with the convenience of
using attributes rather than string keys. It's strongly recommended that you
only use the ``_id`` key when removing items to prevent accidental removal.

.. code-block:: python

   # Remove an individual post
   with Mongo:
      BlogPost.remove({BlogPost._id: post_id})


.. _specifying-indexes:

Specifying Indexes
==================

Indexes are specified using the
:attr:`~humbledb.document.Document.config_indexes` attribute.  This attribute
should be a list of attribute names to index. These names will be automatically
mapped to their key names when the index call is made. More complicated indexes
can be made using the :class:`~humbledb.index.Index` class, which takes the
same areguments as :meth:`~pymongo.collection.Collection.ensure_index`.

HumbleDB uses an :meth:`~pymongo.collection.Collection.ensure_index` call with
a default ``cache_for=`` of 24 hours, and ``background=True``. This will be
called before any :meth:`~pymongo.collection.Collection.find`,
:meth:`~pymongo.collection.Collection.find_one`, or
:meth:`~pymongo.collection.Collection.find_and_modify` operation.

.. versionadded:: 2.2
   :class:`~humbledb.index.Index` class for index creation customization.
.. versionadded:: 3.0
   Support for compound indexes.

.. rubric:: Example: Indexes on a BlogPost class

.. code-block:: python
   :emphasize-lines: 4-5

   class BlogPost(Document):
      config_database = 'humble'
      config_collection = 'posts'
      config_indexes = [
              # Basic indexes
              'author',
              'timestamp',
              # Indexes with additional creation arguments
              Index('tags', sparse=True),
              # Directional indexes with additional creation arguments
              Index([('slug', humbledb.DESC)], unique=True),
              # Embedded indexes
              Index('meta.url')
              # Compound indexes
              Index([('author', humbledb.ASC), ('timestamp', humbledb.DESC)]),
         ]

      timestamp = 'ts'
      author = 'a'
      tags = 'g'
      title = 't'
      slug = 's'
      content = 'c'
      meta = Embed('m')
      meta.url = 'u'

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
* **config_port** (``int``, optional, default:``27017``) - Port to connect to.

.. versionchanged:: 5.2.0

`config_port` is now optional and will default to what
:class:`~pymongo.connection.Connection` will use as default (port 27017).

* **config_replica** (``str``, optional) - Name of the replica set.

If ``config_replica`` is present on the class, then HumbleDB will automatically
use a :class:`~pymongo.connection.ReplicaSetConnection` for you. (Requires
``pymongo >= 2.1``.)

* **config_auth** (``str``, optional) - Username and password.

.. versionadded:: 5.2.0

The `config_auth` string format is identical to how the username and password are
found in a typical `MongoDB-URI
<http://docs.mongodb.org/manual/reference/connection-string/>`_ style
connection string format.

.. rubric:: Global Connection Settings

These settings are available globally through Pyconfig_ configuration keys. Use
either :func:`Pyconfig.set` (i.e. ``pyconfig.set('humbledb.connection_pool',
20)`` or create a Pyconfig_ plugin to change these.

* **humbledb.connection_pool** (``int``, default: ``300``) - Size of the
  connection pool to use.
* **humbledb.allow_explicit_request** (``bool``, default: ``True``) - Whether
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

   # A connection that uses Mongo-CR for basic authentication
   class AuthedDB(Mongo):
       config_host = 'anotherdb.example.com'
       config_auth = 'someuser:secret'

   # Use your custom subclasses as context managers
   with MyDB:
       docs = MyDoc.find({MyDoc.value: {'$gt': 3}})

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

    # A Mongo subclass with authentication credentials will try to
    # authenticate when needed.
    with AuthedDB:
        # No additional authentication calls are necessary!
        one_doc = AnotherDoc.find_one({AnotherDoc.value: 'a string'})


.. _reports:

Pre-aggregated Reports
======================

HumbleDB provides a framework for creating pre-aggregated reports based on the
ideas laid out `here
<http://docs.mongodb.org/manual/use-cases/pre-aggregated-reports/>`_.

These reports are ideal for gathering metrics on a relatively low number of
unique events that happen with a regular frequency. For example, hits to a
certain webpage, or offer signups.

In cases where the event data is sparse, diverse, or has many parameters, other
aggregation approaches may work better.

:note: The documentation on reports is incomplete, and a work in progress.
       Please see the :doc:`api` for more information. If you
       have questions or issues, please contact me via `github issues
       <http://github.com/shakefu/humbledb/issues>`_.

.. versionchanged:: 5.0
   Reports got a full rewrite in version 5 of HumbleDB. They are not backwards
   compatible, but much more useful and efficient. It's highly recommended that
   you migrate old reports to the new classes.

.. rubric:: Example:

::

   from humbledb.report import Report, MONTH, HOUR

   class DailyPageHits(Report):
       """
       This is an example of a class used to record hits to pages.

       This class creates one document per page per month

       This class records the total hits per page per month, as well as the
       hits per page per hour for each hour in the month.

       """
       config_database = 'reports'
       config_collection = 'page_hits'
       config_period = MONTH  # This is the document timeframe
       config_intervals = [MONTH, HOUR]  # Timeframes that data is recorded

   # Record a hit to the /about page
   page = '/about'
   with Mongo:
      DailyPageHits.record(page)

   # Get the last 24 hours worth of hits for /about as a list
   with Mongo:
      hits = DailyPageHits.hourly(page)[-24:]


.. _arrays:

Paginated Arrays
================

One of the limitations of HumbleDB is the performance of very large arrays
within documents, particulary arrays which have indexing on keys within
embedded documents for that array.

There are two issues which arise; first, that each append to the array increases
the array size, which leads to document moves, decreasing the efficiency of the
database, and second, that with each move of a very large array, the indexing
on the whole array must be updated, which can be very slow for arrays over
10,000 elements.

The :class:`humbledb.array.Array` class addresses both of these situations by
first allowing for transparent preallocation of the array document to ensure
that only a minimal number of document moves happen, and second, by
transparently paginating the arrays into multiple documents, to limit the
maximum array size for any single document.

:note: Due to time constrants, the documentation on arrays is incomplete. I
       hope to fix this as soon as possible.

.. rubric:: Example:

::

   from humbledb import Mongo
   from humbledb.array import Array

   class Comments(Array):
       config_database = 'humble'
       config_collection = 'comments'
       config_padding = 10000  # Number of bytes to pad with
       config_max_size = 100  # Number of entries per page

   with Mongo:
       post = BlogPost.find_one(...)  # This is the post associated with
                                      # comments for this example

   comments = Comments(post._id)  # The argument is used to construct the array
                                  # id, which uniquely identifies pages in this
                                  # array. This can be any unique string value

   with Mongo:
       # Appending adds to the Array, creating a new page if necessary, and
       # paginating when an array is too large.
       # The current number of pages is returned
       page_count = comments.append({
               'user_name': "example_user",
               'comment': "I really like arrays.",
               'timestamp': datetime.now(),
               })

       comments.pages()  # Return the current number of pages

       comments.length()  # Return the current number of entries

       entries = comments.all()  # Return all the entries as a list

       first_page = comments[0]  # Return a given page of entries as a list
       pages = comments[0:2]  # Slices work, but negative indexes *do not*

       spec = {'user_name': "example_user"}
       comments.remove(spec)  # Remove all entries matching `spec`

       comments.clear()  # Remove all entries



