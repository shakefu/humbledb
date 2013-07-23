API Documentation
#################

.. contents::
   :local:
   :depth: 2

Documents
=========

.. autoclass:: humbledb.document.Document
   :members:

   See :ref:`documents` for more information.

   .. automethod:: humbledb.document.Document.mapped_keys
   .. automethod:: humbledb.document.Document.mapped_attributes

Embedded Documents
==================

.. autoclass:: humbledb.document.Embed
   :members:

   See :ref:`embedding-documents` for more information.

Indexes
=======

.. autoclass:: humbledb.index.Index
   :members:

   See :ref:`specifying-indexes` for more information.

MongoDB Connections
===================

.. autoclass:: humbledb.mongo.Mongo
   :members:

   See :ref:`subclassing-mongo` for more information.

   .. automethod:: humbledb.mongo.Mongo.start
   .. automethod:: humbledb.mongo.Mongo.end

Reports
=======

The report module contains the HumbleDB reporting framework.

.. autoclass:: humbledb.report.Report
   :members:

Periods/Intervals
-----------------

.. autoattribute:: humbledb.report.YEAR
.. autoattribute:: humbledb.report.MONTH
.. autoattribute:: humbledb.report.DAY
.. autoattribute:: humbledb.report.HOUR
.. autoattribute:: humbledb.report.MINUTE


Arrays
======

.. autoclass:: humbledb.array.Array
   :members:

.. autoclass:: humbledb.array.Page
   :members:

