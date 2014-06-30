"""
Helpers
=======

This module contains common helpers which make your life easier.

"""
from pytool.lang import UNSET

from humbledb import Mongo
from humbledb.errors import NoConnection, DatabaseMismatch


def auto_increment(database, collection, _id, field="value", increment=1):
    """
    Factory method for creating a stored default value which is
    auto-incremented.

    :param database: Database name
    :param collection: Collection name
    :param _id: Unique identifier for auto increment field
    :param field: Sidecar document field name (default: ``"value"``)
    :param increment: Amount to increment counter by (default: 1)
    :type database: str
    :type collection: str
    :type _id: str
    :type field: str
    :type increment: int

    """
    def auto_incrementer():
        """
        Return an auto incremented value.

        """
        # Make sure we're executing in a Mongo connection context
        context = Mongo.context
        if not context:
            raise NoConnection("A connection is required for auto_increment "
                    "defaults to work correctly.")

        if context.database:
            if context.database.name != database:
                raise DatabaseMismatch("auto_increment database %r does not "
                        "match connection database %r")

            # If we have a default database it should already be available
            db = context.database
        else:
            # Otherwise we need to get the correct database
            db = context.connection[database]

        # We just use this directly, instead of using a Document helper
        doc = db[collection].find_and_modify({'_id': _id}, {'$inc': {field:
            1}}, new=True, upsert=True)

        # Return the value
        if not doc:
            # TBD shakefu: Maybe a more specific error here?
            raise RuntimeError("Could not get new auto_increment value for "
                    "%r.%r : %r" % (database, collection, _id))

        value = doc.get('value', UNSET)
        if value is UNSET:
            # TBD shakefu: Maybe a more specific error here?
            raise RuntimeError("Could not get new auto_increment value for "
                    "%r.%r : %r" % (database, collection, _id))

        return value

    return auto_incrementer


