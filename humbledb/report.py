"""
Preaggregated reporting

"""
import pytool

from humbledb.mongo import Document, Embed, Index


class ReportBase(Document):
    """ Superclass for common report methods and fields. """
    # These are just default indexes, but they can be overridden
    config_indexes = [Index('meta.date'), Index('meta.event')]

    meta = Embed('u')
    meta.date = 'd'
    meta.event = 'e'

    def get_id(self, event):
        """ Return an _id value for `event`. """
        raise NotImplementedError("'get_id' must be implemented by a "
                "subclass.")

    def floor_date(self, date):
        """ Return `date` floored to the correct timeframe. """
        raise NotImplementedError("'floor_date' must be implemented by a "
                "subclass.")

    def get_update(self, now):
        """ Return an update dictionary for datetime `now`. """
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
    """ Reports which are aggregated on a daily basis. """
    # Constants used for resolution
    DAILY = 3
    HOUR = 2
    MINUTE = 1

    config_resolution = MINUTE
    """ When subclassed, the `config_resolution` may be set to one of
        :attr:`DailyReport.DAILY`, :attr:`DailyReport.HOUR`,
        :attr:`DailyReport.MINUTE`, to indicate how precise this record should
        be.
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

        if self.config_resolution > self.DAILY:
            raise ValueError("'config_resolution' is not set to a valid "
                    "value.")

        # Increment daily counter always
        update[cls.daily] = 1

        # Increment hour counter if we have at least hourly resolution
        if self.config_resolution <= self.HOUR:
            hour_key = '{}.{}'.format(cls.hour, now.hour)
            update[hour_key] = 1

        # Increment minute counter if we have minute resolution
        if self.config_resolution == self.MINUTE:
            minute_key = '{}.{}.{}'.format(cls.minute, now.hour, now.minute)
            update[minute_key] = 1

        # Create our full update dict
        update = {'$inc': update}

        return update


class WeeklyReport(ReportBase):
    """ Reports which are aggregated on a weekly basis. """
    WEEKLY = 3
    DAY = 2
    HOUR = 1

    config_resolution = HOUR
    """ When subclassed, the `config_resolution` may be set to one of
        :attr:`WeeklyReport.WEEKLY`, :attr:`WeeklyReport.DAY`, or
        :attr:`WeeklyReport.HOUR` to indicate how precise this record should
        be.
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

        if self.config_resolution > self.WEEKLY:
            raise ValueError("'config_resolution' is not set to a valid "
                    "value.")

        # Increment weekly counter always
        update[cls.weekly] = 1

        # Increment day counter if we have at least daily resolution
        if self.config_resolution <= self.DAY:
            day_key = '{}.{}'.format(cls.day, now.day)
            update[day_key] = 1

        # Increment hour counter if we have hour resolution
        if self.config_resolution == self.HOUR:
            hour_key = '{}.{}.{}'.format(cls.hour, now.day, now.hour)
            update[hour_key] = 1

        # Create our full update dict
        update = {'$inc': update}

        return update


class MonthlyReport(ReportBase):
    """ Reports which are aggregated on a monthly basis. """
    MONTHLY = 3
    DAY = 2
    HOUR = 1

    config_resolution = HOUR
    """ When subclassed, the `config_resolution` may be set to one of
        :attr:`MonthlyReport.MONTHLY`, :attr:`MonthlyReport.DAY`, or
        :attr:`MonthlyReport.HOUR` to indicate how precise this record should
        be.
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

        if self.config_resolution > self.MONTHLY:
            raise ValueError("'config_resolution' is not set to a valid "
                    "value.")

        # Increment monthly counter always
        update[cls.monthly] = 1

        # Increment day counter if we have at least daily resolution
        if self.config_resolution <= self.DAY:
            day_key = '{}.{}'.format(cls.day, now.day)
            update[day_key] = 1

        # Increment hour counter if we have hour resolution
        if self.config_resolution == self.HOUR:
            hour_key = '{}.{}.{}'.format(cls.hour, now.day, now.hour)
            update[hour_key] = 1

        # Create our full update dict
        update = {'$inc': update}

        return update


