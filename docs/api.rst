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

ReportBase
----------

.. autoclass:: humbledb.report.ReportBase
   :members:


DailyReport
-----------

.. autoclass:: humbledb.report.DailyReport

   .. automethod:: humbledb.report.DailyReport.record

WeeklyReport
------------

.. autoclass:: humbledb.report.WeeklyReport

   .. automethod:: humbledb.report.DailyReport.record

MonthlyReport
-------------

.. autoclass:: humbledb.report.MonthlyReport

   .. automethod:: humbledb.report.DailyReport.record

Resolutions
-----------

.. autoattribute:: humbledb.report.MONTHLY
.. autoattribute:: humbledb.report.WEEKLY
.. autoattribute:: humbledb.report.DAILY
.. autoattribute:: humbledb.report.HOUR
.. autoattribute:: humbledb.report.MINUTE

