"""
Preaggregated reporting

"""
from pytool.lang import Namespace

from humbledb.mongo import Document


schema = Namespace()
schema.total = 't'
schema.meta.key = 'm'
schema.meta.date = 'd'
schema.meta.tracking = 'k'
schema.event = 'e'
schema.daily = 'd'
schema.hourly = 'h'
schema.minute = 'min'


class Event(Document):
    total = 't'
    meta = 'm'
    event = 'e'


class EventDay(Event):
    hourly = 'h'
    minutes = 'min'


class EventMonth(Event):
    daily = 'd'

