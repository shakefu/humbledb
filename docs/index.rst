.. HumbleDB documentation

.. highlight:: python
.. currentmodule:: humbledb.mongo

.. _Pymongo: http://api.mongodb.org/python/current/
.. _MongoDB: http://www.mongodb.org/
.. _PyPI: http://pypi.python.org/pypi/humbledb
.. _Pytool: http://pypi.python.org/pypi/pytool
.. _Pyconfig: http://pypi.python.org/pypi/pyconfig
.. _github: http://github.com/shakefu/humbledb


===========================
HumbleDB: MongoDB micro-ODM
===========================

HumbleDB is a thin wrapper around Pymongo_ for MongoDB_ that is designed to
make working with flexible schema documents easy and readable.  

* **Flexibility:** A :class:`Document` is also a dictionary, so you have
  maximum flexibility in your code.
* **Attributes:** Short document keys can be mapped to long attribute
  names to keep document size small efficient, while providing very readble
  code.
* **Concurrency:** A context manager is required for any database
  interaciton, minimizing the amount of time a socket is kept out of the
  :py:class:`~pymongo.connection.Connection` pool for the least amount of time
  necessary.

.. rubric:: Example: The humblest document

::

   >>> from humbledb import Mongo, Document
   >>> class HumbleDoc(Document):
   ...     config_database = 'humble'
   ...     config_collection = 'examples'
   ...     description = 'd'
   ...     value = 'v'
   ...     
   >>> doc = HumbleDoc()
   >>> doc.description = "A humble example"
   >>> doc.value = 3.14159265358979
   >>> with Mongo:
   ...     HumbleDoc.insert(doc)
   ...     
   >>> doc
   HumbleDoc({'_id': ObjectId('50c3e72c6112798c3bcde02d'),
      'd': 'A humble example', 'v': 3.14159265358979})

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

