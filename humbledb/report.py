"""
Preaggregated reporting

"""
import pytool

import humbledb
from humbledb import Document, Embed, Index


# Resolutions for reports
MONTHLY = 5
WEEKLY = 4
DAILY = 3
HOUR = 2
MINUTE = 1


class ReportBase(Document):
    """ Document superclass for common report methods and fields. Use this to
        create completely custom pre-aggregate reporting classes.

        **_id**
            Document identifier.

        **meta.date** *= 'u.d'*
            Date of the document.

        **meta.event** *= 'u.e'*
            String identifier for the event.

    """
    # These are just default indexes, but they can be overridden
    config_indexes = [Index([('meta.event', humbledb.ASC), ('meta.date', humbledb.DESC)])]
    """ These are the default indexes. There is a compound index on
    ``meta.event`` and ``meta.date``. """

    meta = Embed('u')
    meta.date = 'd'
    meta.event = 'e'

    def get_id(self, event):
        """ Return an _id value for `event`.

            :note: This must be implemented by a subclass

            :param str event: Event identifier

        """
        raise NotImplementedError("'get_id' must be implemented by a "
                "subclass.")

    def floor_date(self, date):
        """ Return `date` floored to the correct timeframe.

            :note: This must be implemented by a subclass

            :param datetime date: The datetime corresponding to the event

        """
        raise NotImplementedError("'floor_date' must be implemented by a "
                "subclass.")

    def get_update(self, now):
        """ Return an update dictionary for datetime `now`.

            :note: This must be implemented by a subclass

            :param datetime now: The current datetime

        """
        raise NotImplementedError("'get_update' must be implmented by a "
                "subclass.")

    def record(self, event, stamp=None, safe=False):
        """ Records an instance of `event`.

            :param str event: An event key
            :param datetime stamp: A timestamp to use instead of now (optional)
            :param bool safe: Whether to use a safe write to Mongo

        """
        # Get the current time in UTC
        stamp = stamp or pytool.time.utcnow()

        # Set our metadata and _id
        self.meta.event = event
        self.meta.date = self.floor_date(stamp)
        self._id = self.get_id(event)

        # Get our update dict
        update = self.get_update(stamp)

        # Attempt the upsert - this method must be called within a DB context
        # for this to work
        type(self).update(self, update, upsert=True, safe=safe)


class DailyReport(ReportBase):
    """ Reports which are aggregated on a daily basis.

        Subclass this Document to create your own report documents which record
        a day's worth of data per document.

        Example::

            class DailyPageHits(DailyReport):
                config_database = 'reports'
                config_collection = 'page_hits'
                config_resolution = MINUTE

            url_path = '/about'
            DailyPageHits().record(url_path)


        **_id**
            Document identifier like ``'event/20130212'``.

        **meta.date** *= 'u.d'*
            Date of the document.

        **meta.event** *= 'u.e'*
            String identifier for the event.

        **daily** *= 'd'*
            Count of events for this day.

        **hour** `[0..23]` *= 'h'*
            Count per hour. Only used if :attr:`config_resolution` is
            :data:`HOUR` or less.

        **minute** `[0..23][0..59]` *= 'm'*
            Count per minute. Only used :attr:`config_resolution` is
            :data:`MINUTE`.

    """
    config_resolution = MINUTE
    """ When subclassed, the `config_resolution` may be set to one of
        :attr:`DAILY`, :attr:`HOUR`, :attr:`MINUTE`, to indicate how precise
        this record should be.
    """

    daily = 'd'
    hour = 'h'
    minute = 'm'

    def get_id(self, event):
        """ Return an id for `event`. """
        date = self.meta.date or pytool.time.floor_day()
        return '{}/{}{}{}'.format(event, date.year, date.month, date.day)

    def floor_date(self, date):
        """ Return `date` floored to the correct timeframe. """
        return pytool.time.floor_day(date)

    def get_update(self, now):
        """ Return an update dictionary for datetime `now`. """
        # Get the class to reference attribute mappings
        cls = type(self)

        # Start with an empty dictionary, which will become our $inc dict
        update = {}

        if self.config_resolution > DAILY:
            raise ValueError("'config_resolution' is not set to a valid "
                    "value.")

        # Increment daily counter always
        update[cls.daily] = 1

        # Increment hour counter if we have at least hourly resolution
        if self.config_resolution <= HOUR:
            hour_key = '{}.{}'.format(cls.hour, now.hour)
            update[hour_key] = 1

        # Increment minute counter if we have minute resolution
        if self.config_resolution == MINUTE:
            minute_key = '{}.{}.{}'.format(cls.minute, now.hour, now.minute)
            update[minute_key] = 1

        # Create our full update dict
        update = {'$inc': update}

        return update


class WeeklyReport(ReportBase):
    """ Reports which are aggregated on a weekly basis.

        Subclass this Document to create your own report documents which record
        a week's worth of data per document.

        Example::

            class WeeklyPageHits(WeeklyReport):
                config_database = 'reports'
                config_collection = 'page_hits'
                config_resolution = HOUR

            url_path = '/about'
            WeeklyPageHits().record(url_path)


        **_id**
            Document identifier like ``'event/20130212'``.

        **meta.date** *= 'u.d'*
            Date of the start of the week of the document.

        **meta.event** *= 'u.e'*
            String identifier for the event.

        **weekly** *= 'w'*
            Count of events for this week.

        **day** `[0..7]` *= 'd'*
            Count per day. Only used if :attr:`config_resolution` is
            :data:`DAY` or less.

        **hour** `[0..23]` *= 'h'*
            Count per hour. Only used :attr:`config_resolution` is
            :data:`HOUR`.

    """
    config_resolution = HOUR
    """ When subclassed, the `config_resolution` may be set to one of
        :attr:`WEEKLY`, :attr:`DAILY`, or :attr:`HOUR` to indicate how precise
        this record should be.
    """

    weekly = 'w'
    day = 'd'
    hour = 'h'

    def get_id(self, event):
        """ Return an id for `event`. """
        date = self.meta.date or pytool.time.floor_week()
        return '{}/{}{}{}'.format(event, date.year, date.month, date.day)

    def floor_date(self, date):
        """ Return `date` floored to the correct timeframe. """
        return pytool.time.floor_week(date)

    def get_update(self, now):
        """ Return an update dictionary for datetime `now`. """
        # Get the class to reference attribute mappings
        cls = type(self)

        # Create our $inc dict
        update = {}

        if self.config_resolution > WEEKLY or self.config_resolution < HOUR:
            raise ValueError("'config_resolution' is not set to a valid "
                    "value.")

        # Increment weekly counter always
        update[cls.weekly] = 1

        # Increment day counter if we have at least daily resolution
        if self.config_resolution <= DAILY:
            day_key = '{}.{}'.format(cls.day, now.day)
            update[day_key] = 1

        # Increment hour counter if we have hour resolution
        if self.config_resolution == HOUR:
            hour_key = '{}.{}.{}'.format(cls.hour, now.day, now.hour)
            update[hour_key] = 1

        # Create our full update dict
        update = {'$inc': update}

        return update


class MonthlyReport(ReportBase):
    """ Reports which are aggregated on a monthly basis.

        Subclass this Document to create your own report documents which record
        a week's worth of data per document.

        Example::

            class MonthlyPageHits(MonthlyReport):
                config_database = 'reports'
                config_collection = 'page_hits'
                config_resolution = DAY

            url_path = '/about'
            MonthlyPageHits().record(url_path)

        **_id**
            Document identifier like ``'event/201302'``.

        **meta.date** *= 'u.d'*
            Date of the start of the week of the document.

        **meta.event** *= 'u.e'*
            String identifier for the event.

        **monthly** *= 'm'*
            Count of events for this month.

        **day** `[1..31]` *= 'd'*
            Count per day. Only used if :attr:`config_resolution` is
            :data:`DAY` or less.

        **hour** `[1..31][0..23]` *= 'h'*
            Count per hour. Only used :attr:`config_resolution` is
            :data:`HOUR`.

    """
    config_resolution = HOUR
    """ When subclassed, the `config_resolution` may be set to one of
        :attr:`MONTHLY`, :attr:`DAILY`, or :attr:`HOUR` to indicate how
        precise this record should be.
    """

    monthly = 'm'
    day = 'd'
    hour = 'h'

    def get_id(self, event):
        """ Return an id for `event`. """
        date = self.meta.date or pytool.time.utcnow()
        return '{}/{}{}'.format(event, date.year, date.month)

    def floor_date(self, date):
        """ Return `date` floored to the correct timeframe. """
        return pytool.time.floor_month(date)

    def get_update(self, now):
        """ Return an update dictionary for datetime `now`. """
        # Get the class to reference attribute mappings
        cls = type(self)

        # Create our $inc dict
        update = {}

        if self.config_resolution < HOUR:
            raise ValueError("'config_resolution' is not set to a valid "
                    "value.")

        # Increment monthly counter always
        update[cls.monthly] = 1

        # Increment day counter if we have at least daily resolution
        if self.config_resolution <= DAILY:
            day_key = '{}.{}'.format(cls.day, now.day)
            update[day_key] = 1

        # Increment hour counter if we have hour resolution
        if self.config_resolution == HOUR:
            hour_key = '{}.{}.{}'.format(cls.hour, now.day, now.hour)
            update[hour_key] = 1

        # Create our full update dict
        update = {'$inc': update}

        return update

