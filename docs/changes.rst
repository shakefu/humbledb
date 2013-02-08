Changelog
#########

Changes by version
==================

This section contains all the changes that I can remember, by version.

3.0.0
-----

- Major internal refactoring of module layout.
- Add support for compound indexes.
- Add Cursor subclass to do document type coercion rather than use as_class
  argument to pymongo methods.
- Change return value of unset attributes from ``None`` to ``{}``.
- Add aliases :attr:`humbledb.DESC` and :attr:`humbledb.ASC` for
  :attr:`pymongo.DESCENDING` and :attr:`pymongo.ASCENDING` respectively.
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

