"""
Preaggregated reporting

"""
import datetime

import pytool

from humbledb.mongo import Document, Embed, Index


class Report(Document):
    """ Superclass for common report methods and fields. """
    # These are just default indexes, but they can be overridden
    config_indexes = [Index('meta.date'), Index('meta.tag')]

    meta = Embed('u')
    meta.date = 'd'
    meta.event = 'e'

    def _prep(self, _id, date, event):
        """ Turn `self` into a query dictionary, supplying missing values. """
        self._id = self._id or _id
        self.meta.date = self.meta.date or date
        self.meta.event = self.meta.event or event


class DailyReport(Report):
    """ Reports which are aggregated on a daily basis. """
    daily = 'd'
    hour = 'h'
    minute = 'm'

    def record(self, event):
        """ Records a hit for `event`.

            :param str event: A unique event key

        """
        # Get the class to reference attribute mappings
        cls = type(self)

        # Get the current time in UTC
        now = pytool.time.utcnow()

        # Get the current day, which we will use for an index
        day = pytool.time.floor_day(now)

        # Create our event id for the day and prep self to use as a query dict
        _id = '{}{}{}/{}'.format(now.year, now.month, now.day, event)
        self._prep(_id, day, event)

        # Create the dot-notation keys that we'll use for the $inc
        hour_key = '{}.{}'.format(cls.hour, now.hour)
        minute_key = '{}.{}.{}'.format(cls.minute, now.hour, now.minute)

        # Build update dictionary
        update = {
                '$inc': {
                    cls.daily: 1,
                    hour_key: 1,
                    minute_key: 1,
                    }
                }

        # Attempt the upsert - this method must be called within a DB context
        # for this to work
        cls.update(self, update, upsert=True)


class WeeklyReport(Report):
    """ Reports which are aggregated on a weekly basis. """
    hour = 'h'


class MonthlyReport(Report):
    """ Reports which are aggregated on a monthly basis. """
    day = 'd'


