"""
:mod:`humbledb.mongo` module
============================

"""
import logging
import threading
from functools import wraps

import pymongo
import pyconfig
from pytool.lang import classproperty


__all__ = [
        'Mongo',
        'Document',
        ]


class MongoMeta(type):
    """ Metaclass to allow :class:`Mongo` to be used as a context manager
        without having to instantiate it.

    """
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
        if pyconfig.get('me.db.allow_explicit_request', True):
            cls.connection.start_request()
        Mongo.contexts.append(cls)

    def end(cls):
        """ Public function for manually closing a session/context. Should be
            idempotent. This must always be called after :meth:`Mongo.start`
            to ensure the socket is returned to the connection pool.
        """
        if pyconfig.get('me.db.allow_explicit_request', True):
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
            cls._connection.close()
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

    If you need to connect to a different host or port than the default of
    ``'localhost'`` and ``27017``, then you should subclass the :class:`.Mongo`
    class::

        from humbledb import Mongo

        class MyDB(Mongo):
            config_host = 'mongo.mydomain.com'
            config_port = 3001

    And then just use your subclass as you would the :class:`.Mongo` context
    manager::

        with MyDB:
            docs = MyDocument.find({MyDocument.some_field: 1})

    """
    __metaclass__ = MongoMeta
    _self = None
    _connection = None

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
        return pymongo.ReplicaSetConnection(
                host=cls.config_host,
                port=cls.config_port,
                max_pool_size=pyconfig.get('me.db.connection_pool', 10),
                auto_start_request=pyconfig.get('me.db.auto_start_request',
                    True),
                use_greenlets=pyconfig.get('me.db.use_greenlets', False),
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
                max_pool_size=pyconfig.get('me.db.connection_pool', 10),
                auto_start_request=pyconfig.get('me.db.auto_start_request',
                    True),
                use_greenlets=pyconfig.get('me.db.use_greenlets', False),
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


class DictProxyAttribute(object):
    """ Maps long attribute names to convenient/shorter dictionary names. """
    def __init__(self, full_name, name):
        self.full_name = full_name
        self.key = name

    def __get__(self, instance, owner):
        if instance is None:
            return self.key
        return instance.get(self.key, None)

    def __set__(self, instance, value):
        instance[self.key] = value

    def __delete__(self, instance):
        if self.key in instance:
            del instance[self.key]


class CollectionAttribute(object):
    """ Acts as the collection atribute. Refuses to be read unless the
        the executing code is in a :class:`Mongo` context or has already called
        :meth:`Mongo.start`.
    """
    def __get__(self, instance, owner):
        self = instance or owner
        database = self.config_database
        collection = self.config_collection
        # Only allow access to the collection in a Mongo context
        if Mongo.context:
            return Mongo.context.connection[database][collection]
        raise RuntimeError("'collection' not available without context")


class DocumentMeta(type):
    """ Metaclass for Documents. Does a lot of stuff. See :meth:`__new__` for a
        step by step of what this does.
    """
    def __new__(mcs, cls_name, bases, cls_dict):
        # Don't process Document superclass
        if cls_name == 'Document' and bases == (dict,):
            return type.__new__(mcs, cls_name, bases, cls_dict)

        # Handle Document subclasses
        database = None
        collection = None
        reverse = {}

        # Attribute names that conflict with the dict base class
        bad_names = set(['clear', 'collection', 'copy', 'fromkeys', 'get',
                'has_key', 'items', 'iteritems', 'iterkeys', 'itervalues',
                'keys', 'pop', 'popitem', 'setdefault', 'update', 'values',
                'viewitems', 'viewkeys', 'viewvalues'])

        for name in cls_dict.keys():
            if name in bad_names:
                raise TypeError("'{}' bad attribute name".format(name))
            # Ignore names starting with underscore, except _id
            elif name.startswith('_') and name != '_id':
                continue
            # Ignore methods
            elif callable(cls_dict[name]):
                continue

            # Grab the database and collection values
            if name == 'config_database':
                database = cls_dict[name]
                continue
            elif name == 'config_collection':
                collection = cls_dict[name]
                continue
            # Don't proxy the config_indexes attribute
            elif name == 'config_indexes':
                continue

            # Assign proxy attributes to remaining non-private names
            value = cls_dict.pop(name)
            cls_dict[name] = DictProxyAttribute(name, value)
            reverse[value] = name

        if not database or not collection:
            raise TypeError("Missing _database or _collection")

        # Create collection attribute
        cls_dict['collection'] = CollectionAttribute()

        # Create reverse lookup attribute
        cls_dict['_reverse'] = reverse

        # Return new class
        return type.__new__(mcs, cls_name, bases, cls_dict)

    def _wrap(cls, func):
        """ Wraps ``func`` to ensure that it has the as_class keyword
            argument set to ``cls``.

            :param function func: Function to wrap.

        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """ Wrapper function to guarantee indexes. """
            cls._ensure_indexes()
            if 'as_class' not in kwargs:
                kwargs['as_class'] = cls
            return func(*args, **kwargs)
        return wrapper

    def __getattr__(cls, name):
        # Exclude certain names from being passed through
        # __test__ is listed here so nosetests/mocks/something works properly
        if name in ('__test__',):
            raise AttributeError("'{}' has no attribute '{}'".format(
                cls.__name__, name))
        # Allow collection methods to be called directly from class instances
        # but only when in a Mongo context
        if name not in ('config_database', 'config_collection',
                'config_indexes'):
            value = getattr(cls.collection, name, None)
            if not isinstance(value, pymongo.collection.Collection):
                if callable(value):
                    wrap_methods = set(['find', 'find_one', 'find_and_modify'])
                    if name in wrap_methods:
                        value = cls._wrap(value)
                return value
        raise AttributeError("'{}' has no attribute '{}'".format(
            cls.__name__, name))

    @property
    def update(cls):
        """ Method to pass through the *dict*'s update method and instead use
            the collection method.

        """
        return cls.collection.update


class Document(dict):
    """ MongoDB Document class.

        This class is a dictionary subclass designed to provide attribute-style
        access to the underlying dictionary mechanisms, to help support mapping
        of intelligible and descriptive long attribute names to shorter, space
        saving document key names. It holds configuration options for database,
        collection and indexes to be used with a given document. It also
        provides easy access to the corresponding
        :class:`~pymongo.collection.Collection` instance for the given
        database/collection configuration.

        An example document::

            from humbledb import Document

            class Note(Document):
                config_database = 'exampledb'
                config_collection = 'mycollections'
                config_indexes = ['user_name', 'timestamp']

                _id = '_id'
                user_name = 'u'
                html = 'h'
                text = 'x'
                timestamp = 't'

        To access the pymongo :class:`~pymongo.collection.Collection`  instance
        methods, you must first enter into a database connection context. This
        is to ensure that a connection from pymongo's connection pool is held
        for the minimum amount of time needed, to ensure maximum possible
        availability in a concurrent environment.

        Accessing methods::

            from humbledb import Mongo
            from myexample import Note

            with Mongo:
                note = Note.find_one({})

        Creating new document instances works much like you'd expect::

            from humbledb import Mongo
            from myexample import Note

            # Create new instance
            note = Note()
            note.user_name = 'test'
            note.html = '<h1>Hello World</h1>'
            note.text = 'Hello World'

            # Insert into DB with proxied pymongo call
            with Mongo:
                note_id = Note.insert(note)

        When providing query parameters to the pymongo methods, it's best to
        use the long attributes as the key values, rather than the strings
        themselves, for readability and to keep the key names consistent,
        should you want to change one later:

        .. code-block:: python

            from humbledb import Mongo
            from myexample import Note

            with Mongo:
                # Count all notes
                count = Note.find({Note.user_name: 'test'}).count()

                # Find a note's _id
                note_id = Note.find_one({Note.unread: True}, fields=[Note._id])
                note_id = note_id[Note._id]

                # Update a note
                Note.update({Note._id: note_id}, {'$set': {Note.unread: False})

        When accessed at the class level, the attributes simply return the
        string that they're mapped to.

    """
    __metaclass__ = DocumentMeta
    _reverse = None

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
        """ Internal method used by :mod:`simplejson` that we're leveraging to
            do an automatic conversion of keys when serializing to JSON.

        """
        copy = {}
        for key in self.keys():
            if key in self._reverse:
                copy[self._reverse[key]] = self[key]
            else:
                copy[key] = self[key]
        return copy

    @classmethod
    def _ensure_indexes(cls):
        """ Guarantees indexes are created once per connection instance. """
        ensured = getattr(cls, 'ensured', None)
        if ensured:
            return

        if cls.config_indexes:
            for index in cls.config_indexes:
                logging.getLogger(__name__).info("Ensuring index: {}"
                        .format(index))
                getattr(cls, 'collection').ensure_index(getattr(cls, index),
                        background=True,
                        ttl=60*60*24)

        logging.getLogger(__name__).info("Indexing ensured.")
        cls.ensured = True

        # Create a reload hook for the first time we run
        if ensured is None:
            @pyconfig.reload_hook
            def _reload():
                """ Allow index recreation if configuration settings change via
                    pyconfig.
                """
                cls.ensured = False


