"""
"""
import logging
import threading

import pymongo
import pyconfig
from pytool.lang import classproperty, UNSET

from humbledb import _version
from humbledb.errors import (NestedConnection, MissingConfig, InvalidAuth)


__all__ = [
        'Mongo',
        ]

class MongoMeta(type):
    """ Metaclass to allow :class:`Mongo` to be used as a context manager
        without having to instantiate it.

    """
    _connection = None
    _credentials = None
    """ Auth credentials if given. """

    def __new__(mcs, name, bases, cls_dict):
        """ Return the Mongo class. """
        # Choose the correct connection class
        if cls_dict.get('config_connection_cls', UNSET) is UNSET:
            # Are we using a replica?
            # XXX: Getting the connection type at class creation time rather
            # than connection instantiation time means that disabling
            # config_replica (setting to None) at runtime has no effect. I
            # doubt anyone would ever do this, but you never know.
            _replica = cls_dict.get('config_replica', UNSET)
            # Handle attribute descriptors responsibly
            if _replica and hasattr(_replica, '__get__'):
                try:
                    _replica = _replica.__get__(None, None)
                except:
                    raise TypeError("'%s.config_replica' appears to be a "
                            "descriptor and its value could not be "
                            "retrieved reliably." % name)
            # Handle replica set connections
            if _replica:
                if _version._lt('2.1'):
                    raise TypeError("Need pymongo.version >= 2.1 for replica "
                            "sets.")
                elif _version._gte('2.4'):
                    conn = pymongo.MongoReplicaSetClient
                else:
                    conn = pymongo.ReplicaSetConnection
            else:
                # Get the correct regular connection
                if _version._gte('2.4'):
                    conn = pymongo.MongoClient
                else:
                    conn = pymongo.Connection
            # Set our connection type
            cls_dict['config_connection_cls'] = conn

        # Specially handle base class
        if name == 'Mongo' and bases == (object,):
            # Create thread local self
            cls_dict['_self'] = threading.local()
            return type.__new__(mcs, name, bases, cls_dict)

        # Ensure we have minimum configuration params
        if 'config_host' not in cls_dict or cls_dict['config_host'] is None:
            raise TypeError("missing required 'config_host'")

        # Validate that config_auth is acceptable
        _config_auth = cls_dict.get('config_auth', None)
        if _config_auth:
            try:
                cls_dict['_credentials'] = pymongo.uri_parser.parse_userinfo(
                        str(_config_auth))
            except pymongo.errors.InvalidURI:
                raise TypeError("Invalid 'config_auth' value.")

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
            raise NestedConnection("Do not nest a connection within itself, it "
                    "may cause undefined behavior.")
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

    def authenticate(cls, database, username=None, password=None):
        """ Delegates authentication to be the responsibility of the
            context manager.
            .. versionadded: 6.0.0
        """
        # Having no credentials makes this call a noop.
        if not cls.config_auth:
            return

        # Use Mongo class config_auth as defaults if no credentials are
        # passed in.
        if not username or not password:
            username, password = cls._credentials

        if _version._lt('2.5'):
            valid = cls.connection[database].authenticate(username,
                    password)
            if not valid:
                raise InvalidAuth("Invalid database credentials.")
        else:
            try:
                cls.connection[database].authenticate(username, password)
            except pymongo.errors.PyMongoError:
                raise InvalidAuth("Invalid database credentials.")

    def logout(cls, database):
        """ Explicitly deauthorizes the connection client from the database.
            .. versionadded: 6.0.0
        """
        if cls._connection:
            cls._connection[database].logout()

    def __enter__(cls):
        cls.start()

    def __exit__(cls, exc_type, exc_val, exc_tb):
        cls.end()


class Mongo(object):
    """
    Singleton context manager class for managing a single
    :class:`pymongo.connection.Connection` instance.  It is necessary that
    there only be one connection instance for pymongo to work efficiently with
    gevent or threading by using its built in connection pooling.

    This class also manages connection scope, so that we can prevent
    :class:`~humbledb.document.Document` instances from accessing the
    connection outside the context manager scope. This is so that we always
    ensure that :meth:`~pymongo.connection.Connection.end_request` is always
    called to release the socket back into the connection pool, and to restrict
    the scope where a socket is in use from the pool to the absolute minimum
    necessary.

    This class is made to be thread safe.

    Example subclass::

        class MyConnection(Mongo):
            config_host = 'cluster1.mongo.mydomain.com'
            config_port = 27017
            config_auth = 'user:passwd' # Optional authentication.

    Example usage::

        with MyConnection:
            doc = MyDoc.find_one()

    """
    __metaclass__ = MongoMeta
    _self = None

    config_host = 'localhost'
    """ The host name or address to connect to. """

    config_port = None
    """ Optional default port to use if a port is not given. """

    config_auth = None
    """ Optional default authentication value to be for all connections
        to the database if overriding credentials are not found in the
        :class:`~humbledb.document.Document` config_auth attribute.

        Authentication uses MONGODB-CR.

        .. versionadded: 6.0.0
    """

    config_replica = None
    """ If you're connecting to a replica set, this holds its name. """

    config_connection_cls = UNSET
    """ This defines the connection class to use. HumbleDB will try to
    intelligently choose a class based on your replica settings and PyMongo
    version. """

    config_max_pool_size = pyconfig.setting('humbledb.connection_pool', 300)
    """ This specifies the max_pool_size of the connection. """

    config_auto_start_request = pyconfig.setting('humbledb.auto_start_request',
            True)
    """ This specifies the auto_start_request option to the connection. """

    config_use_greenlets = pyconfig.setting('humbledb.use_greenlets', False)
    """ This specifies the use_greenlets option to the connection. """

    config_tz_aware = pyconfig.setting('humbledb.tz_aware', True)
    """ This specifies the tz_aware option to the connection. """

    config_write_concern = pyconfig.setting('humbledb.write_concern', 1)
    """ This specifies the write concern (``w=``) for this connection. This was
        added so that Pymongo before 2.4 will by default use
        ``getLastError()``.

        .. versionadded: 4.0

    """

    def __new__(cls):
        """ This class cannot be instantiated. """
        return cls

    @classmethod
    def _new_connection(cls):
        """ Return a new connection to this class' database. """
        kwargs = {
                'host': cls.config_host,
                'max_pool_size': cls.config_max_pool_size,
                'auto_start_request': cls.config_auto_start_request,
                'use_greenlets': cls.config_use_greenlets,
                'tz_aware': cls.config_tz_aware,
                'w': cls.config_write_concern,
                }
        if cls.config_port:
            kwargs['port'] = cls.config_port

        if cls.config_replica:
            kwargs['replicaSet'] = cls.config_replica
            logging.getLogger(__name__).info("Creating new MongoDB connection "
                    "to '{}:{}' replica: {}".format(cls.config_host,
                        cls.config_port, cls.config_replica))
        else:
            db_location = '{}:{}'.format(cls.config_port,
                    cls.config_host) if cls.config_port else '{}'.format(
                            cls.config_host)
            logging.getLogger(__name__).info("Creating new MongoDB connection "
                "to '{}'".format(db_location))

        return cls.config_connection_cls(**kwargs)

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


