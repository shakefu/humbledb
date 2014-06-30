Changelog
#########

Changes by version
==================

This section contains all the changes that I can remember, by version.

5.3.0
-----

- Add :attr:`~humbledb.mongo.Mongo.config_uri` configuration option for
  declaring default databases and databases with authentication.
- If a :class:`~humbledb.mongo.Mongo` subclass specifies a
  :attr:`~humbledb.mongo.Mongo.config_uri` which includes a database, and a
  :class:`~humbledb.document.Document` is used which does not match the
  database, a :class:`~humbledb.errors.DatabaseMismatch` error will be raised.
- Fix a bug where declaring :class:`~humbledb.mongo.Mongo` subclasses late (at
  runtime) would not correctly instantiate the connection instance.


5.2.0
-----

- :class:`~humbledb.document.Document` declarations can now include default
  values. See :ref:`default-values` for more details.
- :class:`~humbledb.array.Array` regexes now escape periods to prevent name
  collisions.


5.1.4
-----

- Patch from `paulnues <https://github.com/paulnues>`_ to fix brittle tests.

5.1.3
-----

- Bump the default for :attr:`~humbledb.mongo.Mongo.config_max_pool_size` up to
  300, since in PyMongo 2.6, they changed the behavior of connection pools to
  make that a blocking limit, rather than a minimum size.

5.1.2
-----

- Fix a bug where a :class:`~humbledb.report.Report` would raise a ValueError
  on querying months with 30 days.

5.1.1
-----

- Fix a bug where a :class:`~humbledb.array.Array` may not have its page
  created before an append call attempts to modify it by adding write concern
  to the insert.

5.1.0
-----

- Add `count` keyword argument to :meth:`humbledb.report.Report.record` to
  allow recording multiple events instead of always incrementing one.

5.0.1
-----

- Fix a bug with summing report intervals where too many or too few values
  could be returned, sometimes with the wrong timestamp.

5.0.0
-----

- This release may break backwards compatibility.
- Total rewrite of the :module:`humbledb.report` module to make it much more
  useful. Sorry, but I'm fairly sure nobody was
  using it before anyway.

4.0.1
-----

.. currentmodule:: humbledb

- Fix bug with :meth:`array.Array.remove` in sharded environments.

4.0.0
-----

.. currentmodule:: humbledb

- This release may break backwards compatibility.
- Restrict ``from humbledb import *`` to only basic document classes
  (:class:`~mongo.Mongo`, :class:`~document.Document`,
  :class:`~document.Embed`, :class:`~index.Index`).
- Create new :mod:`humbledb.errors` module, which contains shortcuts to Pymongo
  specific errors, as well as the new exceptions: :exc:`~errors.NoConnection`,
  :exc:`~errors.NestedConnection`, and :exc:`~errors.MissingConfig`.
- :class:`~document.Document` will now raise :exc:`~errors.MissingConfig` and
  :exc:`~errors.NoConnection`. The previous behavior was to raise just a
  ``RuntimeError``.
- :class:`~mongo.Mongo` subclasses add the new configuration option
  :attr:`~mongo.Mongo.config_write_concern`. This now defaults to ``1``, which
  may break backwards compatibility. The previous behavior depended on which
  version of Pymongo you were using.
- :class:`~mongo.Mongo` will now raise :exc:`~errors.NestedConnection`.
- :class:`~document.Document` instances which do not map attributes for
  embedded documents will no longer wrap the accessed embedded documents in
  :class:`~maps.DictMap` instances. This should improve performance
  substantially for very large documents with many unmapped, embedded
  documents.
- The :class:`~array.Array` class has been refactored to no longer need the
  ``array_id`` and ``number`` fields, or the index on them. It now leverages
  regex queries against the ``_id`` field instead.
- The :class:`~array.Array` class now has shortcut properties for accessing the
  following attributes on the :class:`~array.Page` class: find, update, remove,
  entries, size. The find, update, and remove attributes require a
  :class:`~mongo.Mongo` (or a subclass) connection context.
- The ``page_count`` parameter to :class:`~array.Array` is not longer required.
  If omitted, the number of pages will be queried for before the first append
  operation.
- :meth:`~array.Array.remove` now only removes the first matching element
  found. The previous behavior was to remove all matching elements, but this
  meant that the :meth:`Array.length` could get out of sync with the actual
  size.

3.3.1
-----

- Now depends on Pytool >= 3.0.1.

3.3.0
-----

- Implement ``for_json()`` hook on :class:`~humbledb.document.Document`,
  :class:`~humbledb.maps.DictMap` and :class:`~humbledb.maps.ListMap`.
- Implement version checking for ``ttl`` vs. ``cache_for`` keyword to
  :func:`ensure_index`.
- Fix :attr:`~humbledb.mongo.Mongo.config_replica` handling when config_replica
  is set to a descriptor class (i.e. a ``pyconfig.setting()`` instance).
- Removed :meth:`humbledb.document.Document._asdict`. Use
  :meth:`~humbledb.document.Document.for_json` instead.

3.2.0
-----

- Add the :mod:`humbledb.array` module and :class:`humbledb.array.Array`
  class for easily working with very large paginated arrays in MongoDB.

3.1.0
-----

- Add support for :class:`~pymongo.MongoClient` and
  :class:`~pymongo.MongoReplicaSetClient`.

3.0.3
-----

- Fix bug in deleting embedded document keys via attributes.

3.0.2
-----

- Fix bug with DocumentMeta accidentally getting extra ``name`` attribute, 
  which in turn became available on Document, and would override mapping
  behavior.

3.0.1
-----

- Fix bug with checking config_resolution on the MonthlyReport.

3.0.0
-----

- Major internal refactoring of module layout.
- Add support for compound indexes.
- Add Cursor subclass to do document type coercion rather than use as_class
  argument to pymongo methods.
- Change return value of unset attributes from ``None`` to ``{}``.
- Add aliases :attr:`humbledb.DESC` and :attr:`humbledb.ASC` for
  :attr:`pymongo.DESCENDING` and :attr:`pymongo.ASCENDING` respectively.
- Add embedded document list attribute mapping.
- Lots of test coverage.

2.3.1
-----

- Change :class:`humbledb.report.DailyReport` to use 0-59 for minute range,
  rather than 0-1439.

2.3.0
-----

- Add support for resolving dot-notation indexes.
- Add reporting framework.

2.2.1
-----

- Fix bug when old version by using pkg_resources.parse_version to check
  pymongo version. 

2.2.0
-----

- Add :class:`~humbledb.index.Index` class.
- Make HumbleDB compatible with ``pymongo >= 2.0.1``.

2.1.1
-----

- Fix bug when find_one or find_and_modify return None.

2.1.0
-----

.. currentmodule:: humbledb.document

- Add :meth:`Document.mapped_keys` and :meth:`Document.mapped_attributes`
  methods.

2.0.2
-----

- Fix bug where find_and_modify returned dict instead of Document subclass.

2.0.1
-----

- Updated documentation.

2.0.0
-----

- First release fit for public consumption.

