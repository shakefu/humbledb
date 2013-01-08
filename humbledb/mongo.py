"""
"""
import logging
import threading
import pkg_resources
from functools import wraps
from collections import deque

import pymongo
import pyconfig
from pytool.lang import UNSET
from pytool.lang import classproperty


__all__ = [
        'Document',
        'Embed',
        'Mongo',
        ]


class MongoMeta(type):
    """ Metaclass to allow :class:`Mongo` to be used as a context manager
        without having to instantiate it.

    """
    _connection = None

    def __new__(mcs, name, bases, cls_dict):
        """ Return the Mongo class. """
        # Specially handle base class
        if name == 'Mongo' and bases == (object,):
            # Create thread local self
            cls_dict['_self'] = threading.local()
            return type.__new__(mcs, name, bases, cls_dict)

        # Ensure we have minimum configuration params
        if 'config_host' not in cls_dict or cls_dict['config_host'] is None:
            raise TypeError("missing required 'config_host'")

        if 'config_port' not in cls_dict or cls_dict['config_port'] is None:
            raise TypeError("missing required 'config_port'")

        # Create new class
        cls = type.__new__(mcs, name, bases, cls_dict)

        # This reload hook uses a closure to access the class
        @pyconfig.reload_hook
        def _reload():
            """ A hook for reloading the connection settings with pyconfig. """
            cls.reconnect()

        return cls

    def start(cls):
        """ Public function for manually starting a session/context. Use
            carefully!
        """
        if cls in Mongo.contexts:
            raise RuntimeError("Do not nest a connection within itself, it may "
                    "cause undefined behavior.")
        if pyconfig.get('humbledb.allow_explicit_request', True):
            cls.connection.start_request()
        Mongo.contexts.append(cls)

    def end(cls):
        """ Public function for manually closing a session/context. Should be
            idempotent. This must always be called after :meth:`Mongo.start`
            to ensure the socket is returned to the connection pool.
        """
        if pyconfig.get('humbledb.allow_explicit_request', True):
            cls.connection.end_request()
        try:
            Mongo.contexts.pop()
        except (IndexError, AttributeError):
            pass

    def reconnect(cls):
        """ Replace the current connection with a new connection. """
        logging.getLogger(__name__).info("Reloading '{}'"
                .format(cls.__name__))
        if cls._connection:
            cls._connection.disconnect()
        cls._connection = cls._new_connection()

    def __enter__(cls):
        cls.start()

    def __exit__(cls, exc_type, exc_val, exc_tb):
        cls.end()


class Mongo(object):
    """
    Singleton class for tracking/holding a single :class:`pymongo.Connection`.
    It is necessary that there only be one connection instance for pymongo to
    work properly with gevent.

    This class also allows tracking whether we're in a session/context scope,
    so that we can prevent :class:`Document` instances from accessing the
    connection independently. This is so that we always ensure that
    :meth:`~pymongo.connection.Connection.end_request` is always called to
    release the socket back into the connection pool.

    This class is made to be thread safe.

    """
    __metaclass__ = MongoMeta
    _self = None

    config_host = 'localhost'
    """ The host name or address to connect to. """
    config_port = 27017
    """ The port to connect to. """
    config_replica = None
    """ If you're connecting to a replica set, this holds its name. """

    def __new__(cls):
        """ This class cannot be instantiated. """
        return cls

    @classmethod
    def _new_replica_connection(cls):
        """ Return a new connection to this class' replica set. """
        logging.getLogger(__name__).info("Creating new MongoDB connection to "
                "'{}:{}' replica: {}".format(cls.config_host, cls.config_port,
                    cls.config_replica))

        if (pkg_resources.parse_version(pymongo.version)
                < pkg_resources.parse_version('2.1')):
            raise RuntimeError("Need pymongo.version >= 2.1 for "
                    "ReplicaSetConnection.")

        return pymongo.ReplicaSetConnection(
                host=cls.config_host,
                port=cls.config_port,
                max_pool_size=pyconfig.get('humbledb.connection_pool', 10),
                auto_start_request=pyconfig.get('humbledb.auto_start_request',
                    True),
                use_greenlets=pyconfig.get('humbledb.use_greenlets', False),
                tz_aware=True,
                replicaSet=cls.config_replica,
                )

    @classmethod
    def _new_connection(cls):
        """ Return a new connection to this class' database. """
        # Handle replica sets separately
        if cls.config_replica:
            return cls._new_replica_connection()

        logging.getLogger(__name__).info("Creating new MongoDB connection to "
                "'{}:{}'".format(cls.config_host, cls.config_port))

        return pymongo.Connection(
                host=cls.config_host,
                port=cls.config_port,
                max_pool_size=pyconfig.get('humbledb.connection_pool', 10),
                auto_start_request=pyconfig.get('humbledb.auto_start_request',
                    True),
                use_greenlets=pyconfig.get('humbledb.use_greenlets', False),
                tz_aware=True)

    @classproperty
    def connection(cls):
        """ Return the current connection. If no connection exists, one is
            created.
        """
        if not cls._connection:
            cls._connection = cls._new_connection()
        return cls._connection

    @classproperty
    def contexts(cls):
        """ Return the current context stack. """
        if not hasattr(Mongo._self, 'contexts'):
            Mongo._self.contexts = []
        return Mongo._self.contexts

    @classproperty
    def context(cls):
        """ Return the current context (a :class:`.Mongo` subclass) if it
            exists or ``None``.
        """
        try:
            return Mongo.contexts[-1]
        except IndexError:
            return None


class CollectionAttribute(object):
    """ Acts as the collection attribute. Refuses to be read unless the
        the executing code is in a :class:`Mongo` context or has already called
        :meth:`Mongo.start`.
    """
    def __get__(self, instance, owner):
        self = instance or owner
        database = self.config_database
        collection = self.config_collection
        if not database or not collection:
            raise RuntimeError("Missing config_database or config_collection")
        # Only allow access to the collection in a Mongo context
        if Mongo.context:
            return Mongo.context.connection[database][collection]
        raise RuntimeError("'collection' not available without context")


class NameMap(unicode):
    """ This class is used to map attribute names to document keys internally.
    """
    def __init__(self, value=''):
        self._key = value.split('.')[-1]
        super(NameMap, self).__init__(value)

    @property
    def key(self):
        # We don't map leading underscore names, so we cheat by storing our key
        # in a private var, and then get it back out again
        return self._key

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __contains__(self, key):
        return key in self.__dict__

    def filtered(self):
        """ Return self.__dict__ minus any private keys. """
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    def mapped(self):
        """ Return the mapped attributes. """
        return self.filtered().keys()

    def merge(self, other):
        """ Merges another `.NameMap` instance into this one. """
        self.__dict__.update(other.filtered())


class DictMap(dict):
    """ This class is used to map embedded documents to their attribute names.
        This class ensures that the original document is kept up to sync with
        the embedded document clones via a reference to the `parent`, which at
        the highest level is the main document.

    """
    def __init__(self, value, name_map, parent, key):
        object.__setattr__(self, '_parent', parent)
        object.__setattr__(self, '_key', key)
        object.__setattr__(self, '_name_map', name_map)
        super(DictMap, self).__init__(value)

    def __getattr__(self, name):
        # Get the mapped attributes
        name_map = object.__getattribute__(self, '_name_map')

        if name not in name_map:
            raise AttributeError("TODO: Check for unmapped keys")

        attr = name_map[name]

        # Get the actual key if we are mapped too deep
        if isinstance(attr, NameMap):
            key = attr.key
        else:
            key = attr

        # Return the value if we have it
        if key in self:
            value = self[key]
            if isinstance(value, dict):
                value = DictMap(value, attr, self, key)
            return value

        if isinstance(attr, NameMap):
            return DictMap({}, attr, self, key)

        # TODO: Decide whether to allow non-mapped keys via attribute access
        object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        # Get the mapped attributes
        name_map = object.__getattribute__(self, '_name_map')
        if name not in name_map:
            raise AttributeError("TODO: Allow setting unmapped keys")

        # If it's mapped, let's map it!
        key = name_map[name]

        if isinstance(key, NameMap):
            key = key.key
        # Assign the mapped key
        self[key] = value

    def __delattr__(self, name):
        # Get the mapped attributes
        name_map = object.__getattribute__(self, '_name_map')
        # If it's mapped, let's map it!
        if name not in name_map:
            object.__delattr__(self, name)
            return

        # If it's mapped, let's map it!
        key = name_map[name]

        if isinstance(key, NameMap):
            key = key.key
        # Delete the key if we have it
        if key in self:
            del self[key]
            return

        # This will attempt a normal delete, and probably raise an error
        object.__delattr__(self, name)

    def __setitem__(self, key, value):
        # Get special attributes
        _key = object.__getattribute__(self, '_key')
        _parent = object.__getattribute__(self, '_parent')

        # The current dictionary may not exist in the parent yet, so we have
        # to create a new one if it's missing
        if _key not in _parent:
            _parent[_key] = {}
        # Keep things synced
        _parent[_key][key] = value

        # Assign to self
        super(DictMap, self).__setitem__(key, value)

    def __delitem__(self, key):
        # Get special attributes
        _key = object.__getattribute__(self, '_key')
        _parent = object.__getattribute__(self, '_parent')

        if _key not in _parent:
            # Fuck it
            return
        # Delete from parent
        if key in _parent[_key]:
            del _parent[_key][key]
            # If this dict is empty, remove it totally from the parent
            if not _parent[_key]:
                del _parent[_key]
        # Delete from self
        if key in self:
            super(DictMap, self).__delitem__(key)
            return
        # Raise an error
        super(DictMap, self).__delitem__(key)


class Embed(unicode):
    """ This class is used to map attribute names on embedded subdocuments.
    """
    def as_name_map(self, base_name):
        name_map = NameMap(base_name)

        for name, value in self.__dict__.items():
            # Skip most everything
            if not isinstance(value, basestring):
                continue
            # Skip private stuff
            if name.startswith('_'):
                continue

            # Concatonate names
            if base_name:
                cname = base_name + '.' + value

            # Recursively map
            if isinstance(value, Embed):
                value = value.as_name_map(cname)
                setattr(name_map, name, value)
            else:
                # Create a new subattribute
                setattr(name_map, name, NameMap(cname))

        return name_map

    def as_reverse_name_map(self, base_name):
        name_map = NameMap(base_name)

        for name, value in self.__dict__.items():
            # Skip most everything
            if not isinstance(value, basestring):
                continue
            # Skip private stuff
            if name.startswith('_'):
                continue

            # Recursively map
            if isinstance(value, Embed):
                reverse_value = value.as_reverse_name_map(name)
            else:
                # Create a new subattribute
                reverse_value = NameMap(name)

            setattr(name_map, value, reverse_value)

        return name_map


class Index(object):
    """ This class is used to create more complex indices. """
    def __init__(self, index, cache_for=60*60*24, background=True, **kwargs):
        # If it's a list or tuple, it includes direction
        if isinstance(index, (tuple, list)):
            self.index, self.direction = index
        else:
            self.index = index
            self.direction = pymongo.ASCENDING

        # Remerge kwargs
        kwargs['cache_for'] = cache_for
        kwargs['background'] = background
        self.kwargs = kwargs

    def ensure(self, cls):
        """ Does an ensure_index call for this index with the given `cls`.

            :param cls: A Document subclass

        """
        index = self.index
        # Map the attribute name to its key name, or just let it ride
        index = getattr(cls, index, index)

        if not isinstance(index, basestring):
            raise TypeError("Invalid index: {!r}".format(self.index))

        cls.collection.ensure_index([(index, self.direction)], **self.kwargs)


class DocumentMeta(type):
    """ Metaclass for Documents. """
    _ignore_attributes = set(['__test__'])
    _collection_methods = set([name for name in
        dir(pymongo.collection.Collection) if not name.startswith('_') and
        callable(getattr(pymongo.collection.Collection, name))])
    _wrapped_methods = set(['find', 'find_one', 'find_and_modify'])
    _update = None

    # Helping pylint with identifying class attributes
    collection = None

    def __new__(mcs, cls_name, bases, cls_dict):
        # Don't process Document superclass
        if cls_name == 'Document' and bases == (dict,):
            return type.__new__(mcs, cls_name, bases, cls_dict)

        # Attribute names that are configuration settings
        config_names = set(['config_database', 'config_collection',
            'config_indexes'])

        # Attribute names that conflict with the dict base class
        bad_names = mcs._collection_methods | set(['clear', 'collection',
            'copy', 'fromkeys', 'get', 'has_key', 'items', 'iteritems',
            'iterkeys', 'itervalues', 'keys', 'pop', 'popitem', 'setdefault',
            'update', 'values', 'viewitems', 'viewkeys', 'viewvalues'])

        # Merge inherited name_maps
        name_map = NameMap()
        reverse_name_map = NameMap()
        for base in reversed(bases):
            if issubclass(base, Document):
                name_map.merge(getattr(base, '_name_map', NameMap()))
                reverse_name_map.merge(getattr(base, '_reverse_name_map',
                    NameMap()))

        # Always have an _id attribute
        if '_id' not in cls_dict and '_id' not in name_map:
            cls_dict['_id'] = '_id'

        # Iterate over the names in `cls_dict` looking for attributes whose
        # values are string literals or `NameMap` subclasses. These attributes
        # will be mapped to document keys where the key is the value
        for name in cls_dict.keys():
            # Raise error on bad attribute names
            if name in bad_names:
                raise TypeError("'{}' bad attribute name".format(name))
            # Skip configuration
            if name in config_names:
                continue
            # Skip most everything
            if not isinstance(cls_dict[name], basestring):
                continue
            # Skip private stuff
            if name.startswith('_') and name != '_id':
                continue

            # Remove the defining attribute from the class namespace
            value = cls_dict.pop(name)
            reverse_value = name

            # Convert Embed objects to nested name map objects
            if isinstance(value, Embed):
                reverse_value = value.as_reverse_name_map(name)
                value = value.as_name_map(value)

            name_map[name] = value
            reverse_name_map[value] = reverse_value

        # Create _*name_map attributes
        cls_dict['_name_map'] = name_map
        cls_dict['_reverse_name_map'] = reverse_name_map

        # Create collection attribute
        cls_dict['collection'] = CollectionAttribute()

        return type.__new__(mcs, cls_name, bases, cls_dict)

    def __getattr__(cls, name):
        # Some attributes need to raise an error properly
        if name in cls._ignore_attributes:
            return object.__getattribute__(cls, name)

        # See if we're looking for a collection method
        if name in cls._collection_methods:
            value = getattr(cls.collection, name, None)
            if name in cls._wrapped_methods:
                value = cls._wrap(value)
            return value

        # Check if we have a mapped attribute name
        name_map = object.__getattribute__(cls, '_name_map')
        if name in name_map:
            return name_map[name]

        # Otherwise, let's just error
        return object.__getattribute__(cls, name)

    def _wrap(cls, func):
        """ Wraps ``func`` to ensure that it has the as_class keyword
            argument set to ``cls``. Also guarantees indexes.

            :param function func: Function to wrap.

        """
        # We have to handle find_and_modify separately because it doesn't take
        # a convenient as_class keyword argument, which is really too bad.
        if func.__name__ == 'find_and_modify':
            @wraps(func)
            def wrapper(*args, **kwargs):
                """ Wrapper function to gurantee object typing and indexes. """
                cls._ensure_indexes()
                doc = func(*args, **kwargs)
                # If doc is not iterable (e.g. None), then this will error
                if doc:
                    doc = cls(doc)
                return doc
            return wrapper

        # If we've made it this far, it's not find_and_modify, and we can do a
        # "normal" wrap.
        @wraps(func)
        def wrapper(*args, **kwargs):
            """ Wrapper function to guarantee indexes. """
            cls._ensure_indexes()
            if 'as_class' not in kwargs:
                kwargs['as_class'] = cls
            return func(*args, **kwargs)
        return wrapper

    def _get_update(cls):
        """ Method to pass through the *dict*'s update method and instead use
            the collection method.

        """
        return cls._update or cls.collection.update

    def _set_update(cls, value):
        """ Allows setting the update attribute for testing with mocks. """
        cls._update = value

    def _del_update(cls):
        """ Allows deleting the update attribute for testing with mocks. """
        cls._update = None

    def mapped_keys(cls):
        """ Return a list of the mapped keys. """
        return cls._reverse_name_map.mapped()

    def mapped_attributes(cls):
        """ Return a list of the mapped attributes. """
        return cls._name_map.mapped()

    update = property(_get_update, _set_update, _del_update)


class Document(dict):
    """ This class represents a Mongo document. """
    __metaclass__ = DocumentMeta

    collection = None

    config_database = None
    """ Database name for this document. """
    config_collection = None
    """ Collection name for this document. """
    config_indexes = None
    """ Indexes for this document. """

    def __repr__(self):
        return "{}({})".format(
                self.__class__.__name__,
                super(Document, self).__repr__())

    def _asdict(self):
        """ Return this document as a dictionary, with short key names mapped
            to long names. This method is used by simplejson and
            :meth:`pytools.json.as_json`.
        """
        # Get the reverse mapped keys
        reverse_name_map = object.__getattribute__(self, '_reverse_name_map')

        def mapper(doc, submap):
            copy = {}
            for key, value in doc.items():
                if isinstance(value, dict) and key in submap:
                    copy[submap[key]] = mapper(value, submap[key])
                elif key in submap:
                    copy[submap[key]] = value
                else:
                    copy[key] = value

            return copy

        return mapper(self, reverse_name_map)

    def __getattr__(self, name):
        # Get the mapped attributes
        name_map = object.__getattribute__(self, '_name_map')
        # If the attribute is mapped, map it!
        if name in name_map:
            name_map = name_map[name]
            # Check if we actually have a key for that value
            if name_map in self:
                value = self[name_map]
                # If it's a dict, we need to keep mapping subkeys
                if isinstance(value, dict):
                    value = DictMap(value, name_map, self, name_map)
                return value
            elif isinstance(name_map, NameMap):
                # Return an empty dict map to allow sub-key assignment
                return DictMap({}, name_map, self, name_map)
            else:
                # Return none if a mapped attribute is missing
                return None

        # TODO: Decide whether to allow non-mapped keys via attribute access
        object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        # Get the mapped attributes
        name_map = object.__getattribute__(self, '_name_map')
        # If it's mapped, let's map it!
        if name in name_map:
            key = name_map[name]
            if isinstance(key, NameMap):
                key = key.key
            # Assign the mapped key
            self[key] = value
            return

        # TODO: Decide whether to allow non-mapped keys via attribute access
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        # Get the mapped attributes
        name_map = object.__getattribute__(self, '_name_map')
        # If we have the key, we delete it
        if name in name_map:
            key = name_map[name]
            if isinstance(key, NameMap):
                key = key.key
            del self[key]
            return

        object.__delattr__(self, name)

    def __setitem__(self, key, value):
        # Pymongo will attempt to use the document subclass for all embedded
        # documents, which we don't want
        if isinstance(value, Document):
            value = dict(value)
        super(Document, self).__setitem__(key, value)

    @classmethod
    def _ensure_indexes(cls):
        """ Guarantees indexes are created once per connection instance. """
        ensured = getattr(cls, '_ensured', None)
        if ensured:
            return

        if cls.config_indexes:
            for index in cls.config_indexes:
                logging.getLogger(__name__).info("Ensuring index: {}"
                        .format(index))
                if isinstance(index, Index):
                    index.ensure(cls)
                else:
                    cls.collection.ensure_index(getattr(cls, index),
                            background=True,
                            cache_for=60*60*24)

        logging.getLogger(__name__).info("Indexing ensured.")
        cls._ensured = True

        # Create a reload hook for the first time we run
        if ensured is None:
            @pyconfig.reload_hook
            def _reload():
                """ Allow index recreation if configuration settings change via
                    pyconfig.
                """
                cls._ensured = False
