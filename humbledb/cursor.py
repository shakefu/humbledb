"""
"""
import six
import pymongo

from humbledb import _version


class Cursor(pymongo.cursor.Cursor):
    """ This subclass of :class:`pymongo.cursor.Cursor` is used to ensure that
        documents are coerced to the correct type as they are returned by the
        cursor.

    """
    # This class works by assigning a different class to this variable in a
    # cursor instance
    _doc_cls = dict

    def next(self):
        if six.PY3 and _version._gte('3'):
            doc = super().next()
        elif six.PY3 and _version._lt('3'):
            doc = super().__next__()
        else:
            doc = super(Cursor, self).next()
        doc = self._doc_cls(doc)
        return doc

    __next__ = next

    def __getitem__(self, index):
        doc = super(Cursor, self).__getitem__(index)
        return self._doc_cls(doc)

    def __clone(self, deepcopy=True):
        """ This is a direct copy of pymongo 2.4's __clone method. This is a
            pretty fragile implementation since it relies on copying private
            variables...
        """
        clone = type(self)(self.__collection)
        values_to_clone = ("spec", "fields", "skip", "limit",
                           "timeout", "snapshot", "tailable",
                           "ordering", "explain", "hint", "batch_size",
                           "max_scan", "as_class", "slave_okay", "await_data",
                           "partial", "manipulate", "read_preference",
                           "tag_sets", "secondary_acceptable_latency_ms",
                           "must_use_master", "uuid_subtype", "query_flags",
                           "kwargs")
        more_values_to_clone = ('_doc_cls',)
        data = dict((k, v) for k, v in six.iteritems(self.__dict__)
                    if (k.startswith('_Cursor__') and k[9:] in values_to_clone)
                    or (k in more_values_to_clone))
        if deepcopy and hasattr(self, '__deepcopy'):
            data = self.__deepcopy(data)
        clone.__dict__.update(data)
        return clone

    def clone(self):
        """Get a clone of this cursor.

        Returns a new Cursor instance with options matching those that have
        been set on the current instance. The clone will be completely
        unevaluated, even if the current instance has been partially or
        completely evaluated.

        """
        return self.__clone(True)

    def __copy__(self):
        return self.__clone(deepcopy=False)

    def __deepcopy__(self, memo):
        return self.__clone(deepcopy=True)

