"""
"""


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
        return {k: v for k, v in self.__dict__.items() if not
                k.startswith('_')}

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
            raise AttributeError("{!r} is not mapped".format(name))

        attr = name_map[name]

        print attr, type(attr)
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
            raise AttributeError("{!r} is not a mapped attribute".format(name))

        # If it's mapped, let's map it!
        key = name_map[name]

        if isinstance(key, NameMap):
            key = key.key
        # Assign the mapped key
        self[key] = value

    def __delattr__(self, name):
        # Get the mapped attributes
        name_map = object.__getattribute__(self, '_name_map')
        # If it's not mapped, let's delete it!
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


