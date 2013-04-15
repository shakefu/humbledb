import itertools

import humbledb
from humbledb import Document, Index


class Page(Document):
    """ Document class used by :class:`Array`. """
    config_indexes = [Index([('array_id', 1), ('number', 1)])]

    array_id = 'i'  # _id of Array group of docs
    number = 'n'  # Page number
    size = 's'   # Number of entries in this page
    entries = 'e'  # Array of entries


class ArrayMeta(type):
    """
    MetaClass for Arrays. This ensures that we have all the needed
    configuration options, as well as creating the :class:`Page` subclass.

    """
    def __new__(mcs, name, bases, cls_dict):
        # Skip the Array base clas
        if name == 'Array' and bases == (object,):
            return type.__new__(mcs, name, bases, cls_dict)
        # The dictionary for subclassing the Page document
        page_dict = {}
        # Check for required class members
        for member in 'config_database', 'config_collection':
            if member not in cls_dict:
                raise TypeError("{!r} missing required {!r}".format(name,
                    member))
            # Move the config to the page
            page_dict[member] = cls_dict.pop(member)
        # Create our page subclass
        cls_dict['_page'] = type(name + 'Page', (Page,), page_dict)
        # Return our new Array
        return type.__new__(mcs, name, bases, cls_dict)


class Array(object):
    """
    HumbleDB Array object. This helps manage paginated array documents in
    MongoDB. This class is designed to be inherited from, and not instantiated
    directly.

    :param str _id: Array _id
    :param int page_count: Total number of pages that already exist

    """
    __metaclass__ = ArrayMeta

    config_max_size = 500
    """ Soft limit on the maximum number of entries per page. """

    config_page_marker = u'#'
    """ Combined with the array_id and page number to create the page _id. """

    config_padding = 0
    """ Number of bytes to pad new page creation with. """

    def __init__(self, _id, page_count):
        self.array_id = _id
        self.page_count = page_count

    def page_id(self, page_number):
        """
        Return the document ID for `page_number`.

        :param int page_number: A page number

        """
        return "{}{}{}".format(self.array_id, self.config_page_marker,
                page_number)

    def new_page(self, page_number):
        """
        Creates a new page document.

        :param int page_number: The page number to create

        """
        # Shortcut the page class
        Page = self._page
        # Create a new page instance
        page = Page()
        page._id = self.page_id(page_number)
        page.array_id = self.array_id
        page.number = page_number
        page.size = 0
        page.entries = []
        page['padding'] = '0' * self.config_padding
        # Insert the new page
        try:
            Page.insert(page, safe=True)
        except humbledb.errors.DuplicateKeyError:
            # A race condition already created this page, so we are done
            return
        # Remove the padding
        Page.update({Page._id: page._id}, {'$unset': {'padding': 1}},
                safe=True)

    def append(self, entry):
        """
        Append an entry to this array and return the page count.

        :param dict entry: New entry
        :returns: Total number of pages

        """
        # See if we have to create our initial page
        if self.page_count < 1:
            self.page_count = 1
            self.new_page(self.page_count)
        # Shortcut page class
        Page = self._page
        # Append our entry to our page and get the page's size
        page = Page.find_and_modify({Page.array_id: self.array_id, Page.number:
            self.page_count}, {'$inc': {Page.size: 1}, '$push': {Page.entries:
                entry}}, new=True, fields={Page.size: 1})
        if not page:
            raise RuntimeError("Append failed: page does not exist.")
        # If we need to, we create the next page
        if page.size >= self.config_max_size:
            self.page_count += 1
            self.new_page(self.page_count)
        # Return the page count
        return self.page_count

    def remove(self, spec):
        """
        Remove `spec` from this array.

        :param dict spec: Dictionary matching items to be removed

        """
        Page = self._page
        result = Page.update({Page.array_id: self.array_id, Page.entries:
            spec}, {'$pull': {Page.entries: spec}, '$inc': {Page.size: -1}},
            multi=True, safe=True)
        # Check the result
        if 'updatedExisting' in result and result['updatedExisting']:
            return True
        return False

    def _all(self):
        """ Return a cursor for iterating over all the pages. """
        Page = self._page
        return Page.find({Page.array_id: self.array_id})

    def all(self):
        """ Return all entries in this array. """
        cursor = self._all()
        return list(itertools.chain.from_iterable(p.entries for p in cursor))

    def clear(self):
        """ Remove all documents in this array. """
        self._page.remove({self._page.array_id: self.array_id}, safe=True)
        self.page_count = 0

    def length(self):
        """ Return the total number of items in this array. """
        # This is implemented rather than __len__ because it incurs a query,
        # and we don't want to query transparently
        Page = self._page
        cursor = Page.find({Page.array_id: self.array_id}, fields={Page.size:
            1, Page._id: 0})
        return sum(p.size for p in cursor)

    def pages(self):
        """ Return the total number of pages in this array. """
        Page = self._page
        return Page.find({Page.array_id: self.array_id}).count()

    def __getitem__(self, index):
        """
        Return a page or pages for the given index or slice respectively.

        :param index: Integer index or ``slice()`` object

        """
        if not isinstance(index, (int, slice)):
            raise TypeError("Array indices must be integers, not %s" %
                    type(index))
        Page = self._page  # Shorthand the Page class
        # If we have an integer index, it's a simple query for the page number
        if isinstance(index, int):
            if index < 0:
                raise IndexError("Array indices must be positive")
            # Page numbers are not zero indexed
            index += 1
            page = Page.find_one({Page.array_id: self.array_id, Page.number:
                index})
            if not page:
                raise IndexError("Array index out of range")
            return page.entries
        # If we have a slice, we attempt to get the pages for [start, stop)
        if isinstance(index, slice):
            if index.step:
                raise TypeError("Arrays do not allow extended slices")
            # Page numbers are not zero indexed
            start = index.start + 1
            stop = index.stop + 1
            cursor = Page.find({Page.array_id: self.array_id, Page.number:
                {'$gte': start, '$lt': stop}})
            return list(itertools.chain.from_iterable(p.entries for p in
                cursor))
        # This comment will never be reached

