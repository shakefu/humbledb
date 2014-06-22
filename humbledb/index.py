"""
"""
from pytool.lang import UNSET

from humbledb import _version


class Index(object):
    """ This class is used to create more complex indices. Takes the same
        arguments and keyword arguments as
        :meth:`~pymongo.collection.Collection.ensure_index`.

        Example::

            class MyDoc(Document):
                config_database = 'db'
                config_collection = 'example'
                config_indexes = [Index('value', sparse=True)]

                value = 'v'

        .. versionadded:: 2.2

    """
    def __init__(self, index, cache_for=(60 * 60 * 24), background=True,
            **kwargs):
        self.index = index

        # Merge kwargs
        kwargs['cache_for'] = cache_for
        kwargs['background'] = background

        if _version._lt('2.3') and 'cache_for' in kwargs:
            kwargs['ttl'] = kwargs.pop('cache_for')

        self.kwargs = kwargs

    def ensure(self, cls):
        """ Does an ensure_index call for this index with the given `cls`.

            :param cls: A Document subclass

        """
        # Map the attribute name to its key name, or just let it ride
        index = self._resolve_index(cls)

        # Authenticate if necessary as ensure_index fails when called outside
        # of the Mongo context manager's bounds.
        cls.authenticate()

        # Make the ensure index call
        cls.collection.ensure_index(index, **self.kwargs)

    def _resolve_index(self, cls):
        """ Resolves an index to its actual dot notation counterpart, or
            returns the index as is.

            :param cls: A Document subclass
            :param str index: Index to resolve

        """
        # If we have just a string, it's a simple index
        if isinstance(self.index, basestring):
            return self._resolve_name(cls, self.index)

        # Otherwise it must be an iterable
        for i in xrange(len(self.index)):
            # Of 2-tuples
            pair = self.index[i]
            if len(pair) != 2:
                raise TypeError("Invalid index: {!r}".format(self.index))
            # Where the first is the key, and the second the direction
            self.index[i] = (self._resolve_name(cls, pair[0]), pair[1])

        return self.index

    def _resolve_name(self, cls, name):
        """ Resolve a dot notation index name to its real document keys. """
        attrs = name.split('.')
        part = cls
        while attrs:
            attr = attrs.pop(0)
            part = getattr(part, attr, UNSET)
            if part is UNSET:
                return name
        if not isinstance(part, basestring):
            raise TypeError("Invalid key: {!r}".format(part))
        return part

    def __repr__(self):
        return "{}({!r}, **{!r})".format(type(self).__name__, self.index,
                self.kwargs)

