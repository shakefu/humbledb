"""
"""
import pymongo
from pytool.lang import UNSET


class Index(object):
    """ This class is used to create more complex indices.

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
        index = self._resolve_index(cls, index)
        # Make the ensure index call
        cls.collection.ensure_index(index, **self.kwargs)

    def _resolve_index(self, cls, index):
        """ Resolves an index to its actual dot notation counterpart, or
            returns the index as is.

            :param cls: A Document subclass
            :param str index: Index to resolve

        """
        # If we have just a string, it's a simple index
        if isinstance(index, basestring):
            return self._resolve_name(cls, index)

        # Otherwise it must be an iterable
        for i in xrange(len(index)):
            if len(index[i]) != 2:
                raise TypeError("Invalid index: {!r}".format(index))
            index[i] = (self._resolve_name(cls, index[i][0]), index[i][1])

        return index

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

