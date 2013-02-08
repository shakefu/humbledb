"""
"""
import logging
import threading
import pkg_resources

import pymongo
import pyconfig
from pytool.lang import classproperty


__all__ = [
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
            raise RuntimeError("Do not nest a connection within itself, it "
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


