# HumbleDB - MongoDB Object-Document Mapper

HumbleDB solves the age-old MongoDB dilemma: write readable, maintainable code
or optimize for storage efficiency. With HumbleDB, you get both. This
lightweight ODM lets you use clear, descriptive attribute names in your Python
code while automatically mapping them to ultra-short database keys,
dramatically reducing document size and memory usage without sacrificing code
clarity.

[![CI](https://github.com/shakefu/humbledb/actions/workflows/ci.yaml/badge.svg)](https://github.com/shakefu/humbledb/actions)
[![Coverage Status](https://coveralls.io/repos/shakefu/humbledb/badge.png?branch=master)](https://coveralls.io/r/shakefu/humbledb?branch=master)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/shakefu?style=flat&logo=github&logoColor=white&labelColor=ea4aaa&color=ea4aaa)](https://github.com/sponsors/shakefu)

> [!WARNING] Version 7.0.0 Breaking Changes
> This release updates to Pymongo 4.x, which introduces [breaking
> changes](https://pymongo.readthedocs.io/en/stable/migrate-to-pymongo4.html).
> While we've maintained all older 3.x and 2.x Pymongo methods with identical
> signatures where possible, there may be other breaking changes not covered by
> our test suite. If you encounter any issues during upgrade, please [open an
> issue](https://github.com/shakefu/humbledb/issues/new/choose).

## Features

**Efficient Storage**: Map readable attribute names to ultra-short database keys,
reducing document size and memory usage while maintaining code clarity.

**Full Pymongo Compatibility**: Maintains backwards-compatible methods for
Pymongo 4.x including `insert`, `find_and_modify`, `save`, and other familiar
operations.

**Maximum Flexibility**: Documents are also dictionaries - no schema
restrictions, maximum adaptability to changing requirements.

**Thread & Greenlet Safe**: Built for concurrent applications with safe
connection handling and resource management.

**Context-Managed Connections**: [Connection paradigm](https://humbledb.readthedocs.io/en/latest/tutorial.html#configuring-connections)
minimizes socket usage from the connection pool through explicit context
managers.

**Lightweight Design**: Thin wrapper around Pymongo that exposes the full power
of the underlying driver without performance overhead.

## Quick Start

### Define Your Document Schema

Create a [`Document`](https://humbledb.readthedocs.io/en/latest/api.html#documents)
subclass with readable attribute names mapped to short database keys:

```python
from humbledb import Mongo, Document

class TestDoc(Document):
    config_database = 'test'      # Target database
    config_collection = 'testdoc' # Target collection
    test_key = 't'               # Maps 'test_key' attribute to 't' in MongoDB
    other_key = 'o'              # Maps 'other_key' attribute to 'o' in MongoDB
```

### Create and Populate Documents

Documents work like regular Python objects with attribute access, while storing
data efficiently:

```python
doc = TestDoc()
doc.test_key = 'Hello'
doc.other_key = 'World'

# View the actual MongoDB document structure
print(doc)
# TestDoc({'t': 'Hello', 'o': 'World'})
```

### Flexible Data Access

Access your data through mapped attributes or direct dictionary keys:

```python
# Via mapped attributes (recommended)
print(doc.test_key)    # 'Hello'

# Via dictionary access
print(doc['t'])        # 'Hello'
print(doc['o'])        # 'World'
```

### Database Operations

Use the [`Mongo`](https://humbledb.readthedocs.io/en/latest/api.html#mongodb-connections)
context manager for safe database operations:

```python
# Insert document
with Mongo:
    TestDoc.insert(doc)

# Query documents
with Mongo:
    found = TestDoc.find_one()

print(found)
# TestDoc({'_id': ObjectId('50ad81586112797f89b99606'), 't': 'Hello', 'o': 'World'})
```

See the documentation for more examples and detailed explanations.

## Documentation

The complete documentation can be found on <http://humbledb.readthedocs.org>.

## License

See LICENSE.rst.

## Contributors

- [shakefu](https://github.com/shakefu) (Creator, Maintainer)
- [paulnues](https://github.com/paulnues)
