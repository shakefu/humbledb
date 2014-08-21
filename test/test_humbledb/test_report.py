import calendar
import datetime

import pytool
from nose.tools import raises

from humbledb import report
from ..util import DBTest, database_name, eq_, ok_
from humbledb.report import (Report, YEAR, MONTH, DAY, HOUR, MINUTE)


class Yearly(Report):
    config_database = database_name()
    config_collection = 'report.year'
    config_period = YEAR
    config_intervals = [YEAR, DAY]


class Monthly(Report):
    config_database = database_name()
    config_collection = 'report.month'
    config_period = MONTH
    config_intervals = [MONTH, HOUR]


class Daily(Report):
    config_database = database_name()
    config_collection = 'report.day'
    config_period = DAY
    config_intervals = [DAY, MINUTE]


class Full(Report):
    config_database = database_name()
    config_collection = 'report.day'
    config_period = YEAR
    config_intervals = [YEAR, MINUTE]


class ByHour(Report):
    config_database = database_name()
    config_collection = 'report.by_hour'
    config_period = DAY
    config_intervals = [DAY, HOUR]


def teardown():
    DBTest.connection.drop_database(database_name())


def test_update_clause_creates_dot_notated_clause():
    stamp = datetime.datetime(2013, 1, 5, 7, 9, 0, tzinfo=pytool.time.UTC())

    eq_(Yearly._update_clause(YEAR, stamp), {Yearly.year: 1})
    eq_(Yearly._update_clause(MONTH, stamp), {Yearly.month + '.0': 1})
    eq_(Yearly._update_clause(DAY, stamp), {Yearly.day + '.0.4': 1})
    eq_(Yearly._update_clause(HOUR, stamp), {Yearly.hour + '.0.4.7': 1})
    eq_(Yearly._update_clause(MINUTE, stamp), {Yearly.minute + '.0.4.7.9': 1})

    eq_(Monthly._update_clause(YEAR, stamp), {Monthly.year: 1})
    eq_(Monthly._update_clause(MONTH, stamp), {Monthly.month: 1})
    eq_(Monthly._update_clause(DAY, stamp), {Monthly.day + '.4': 1})
    eq_(Monthly._update_clause(HOUR, stamp), {Monthly.hour + '.4.7': 1})
    eq_(Monthly._update_clause(MINUTE, stamp), {Monthly.minute + '.4.7.9': 1})

    eq_(Daily._update_clause(YEAR, stamp), {Daily.year: 1})
    eq_(Daily._update_clause(MONTH, stamp), {Daily.month: 1})
    eq_(Daily._update_clause(DAY, stamp), {Daily.day: 1})
    eq_(Daily._update_clause(HOUR, stamp), {Daily.hour + '.7': 1})
    eq_(Daily._update_clause(MINUTE, stamp), {Daily.minute + '.7.9': 1})


def test_record_event_yearly():
    event = 'yearly_record_event'
    now = pytool.time.utcnow()
    with DBTest:
        Yearly.record(event, now)
        doc = Yearly.find_one()

    eq_(doc.meta.event, event)
    eq_(doc.meta.period, Yearly._period(now))

    eq_(len(doc.day), 12)
    for month in doc.day:
        ok_(len(month) >= 28)

    eq_(doc.year, 1)
    eq_(doc.day[now.month-1][now.day-1], 1)

    with DBTest:
        Yearly.record(event, now)
        doc = Yearly.find_one()

    eq_(doc.year, 2)
    eq_(doc.day[now.month-1][now.day-1], 2)


def test_record_event_monthly():
    event = 'monthly_record_event'
    now = pytool.time.utcnow()
    with DBTest:
        Monthly.record(event, now)
        doc = Monthly.find_one()

    eq_(doc.meta.event, event)
    eq_(doc.meta.period, Monthly._period(now))

    ok_(len(doc.hour) >= 28)
    for day in doc.hour:
        eq_(len(day), 24)

    eq_(doc.month, 1)
    eq_(doc.hour[now.day-1][now.hour], 1)

    with DBTest:
        Monthly.record(event, now)
        doc = Monthly.find_one()

    eq_(doc.month, 2)
    eq_(doc.hour[now.day-1][now.hour], 2)


def test_record_event_daily():
    event = 'daily_record_event'
    now = pytool.time.utcnow()
    with DBTest:
        Daily.record(event, now)
        doc = Daily.find_one()

    eq_(doc.meta.event, event)
    eq_(doc.meta.period, Daily._period(now))

    eq_(len(doc.minute), 24)
    for minute in doc.minute:
        eq_(len(minute), 60)

    eq_(doc.day, 1)
    eq_(doc.minute[now.hour][now.minute], 1)

    with DBTest:
        Daily.record(event, now)
        doc = Daily.find_one()

    eq_(doc.day, 2)
    eq_(doc.minute[now.hour][now.minute], 2)


def test_preallocate_future():
    class PreallocAlways(Report):
        config_database = database_name()
        config_collection = 'prealloc'
        config_period = MONTH
        config_intervals = [MONTH, HOUR]
        config_preallocation = 1

    event = 'prealloc_future'
    now = pytool.time.utcnow()

    with DBTest:
        PreallocAlways.record(event, now)
        eq_(PreallocAlways.find().count(), 2)

        # Ensure we don't preallocate too many
        PreallocAlways._preallocated[PreallocAlways._period(now)].remove(event)
        PreallocAlways.record(event)
        eq_(PreallocAlways.find().count(), 2)


def test_report_query_by_hour():
    now = pytool.time.utcnow()
    event = 'event_test_report_query_by_hour'
    with DBTest:
        ByHour.record(event, now)
        ByHour.record(event, now - datetime.timedelta(seconds=60*60))
        counts = ByHour.hourly(event)[-3:]

    eq_(counts, [0, 1, 1])


def test_report_query_by_hour_across_edge():
    stamp = datetime.datetime(2013, 1, 1, tzinfo=pytool.time.UTC())
    stamp2 = stamp - datetime.timedelta(seconds=60*60)
    event = 'event_test_report_query_by_hour_edge'
    with DBTest:
        ByHour.record(event, stamp)
        ByHour.record(event, stamp2)
        stamp += datetime.timedelta(seconds=60*60+1)
        stamp2 -= datetime.timedelta(seconds=60*60)
        counts = ByHour.hourly(event)[stamp2:stamp]

    eq_(counts, [0, 1, 1, 0])
    eq_([c.year for c in counts], [2012, 2012, 2013, 2013])
    eq_([c.month for c in counts], [12, 12, 1, 1])
    eq_([c.hour for c in counts], [22, 23, 0, 1])
    eq_([c.minute for c in counts], [0] * 4)


@raises(ValueError)
def test_resolution_error():
    ByHour.per_minute


@raises(TypeError)
def test_index_error():
    ByHour.hourly[-1]


@raises(TypeError)
def test_extended_slice_error():
    ByHour.hourly[2:3:4]


def test_report_query_monthly_by_yearly():
    stamp = pytool.time.utcnow()
    stamp = stamp.replace(hour=1, minute=0, second=0, microsecond=0)
    hour = datetime.timedelta(seconds=60*60)
    event = 'event_report_query_monthly_by_yearly'
    with DBTest:
        Monthly.record(event, stamp)
        Monthly.record(event, stamp + hour)
        Monthly.record(event, stamp + hour + hour)

        counts = Monthly.yearly(event)[-1:]
        eq_(counts, [3])
        count = counts[0]
        eq_(count.timestamp.timetuple()[:1], stamp.timetuple()[:1])
        eq_(count.month, 1)
        eq_(count.day, 1)
        eq_(count.hour, 0)


def test_report_query_monthly_by_monthly():
    stamp = pytool.time.utcnow()
    stamp = report._relative_period(report.MONTH, stamp, -1)
    stamp = stamp.replace(hour=1, minute=0, second=0, microsecond=0)
    hour = datetime.timedelta(seconds=60*60)
    event = 'event_report_query_monthly_by_monthly'
    with DBTest:
        Monthly.record(event, stamp)
        Monthly.record(event, stamp + hour)
        Monthly.record(event, stamp + hour + hour)

        counts = Monthly.monthly(event)[-2:-1]
        eq_(counts, [3])
        count = counts[0]
        eq_(count.timestamp.timetuple()[:2], stamp.timetuple()[:2])
        eq_(count.day, 1)
        eq_(count.hour, 0)


def test_report_query_monthly_by_daily():
    stamp = pytool.time.utcnow()
    stamp -= datetime.timedelta(days=1)
    stamp = stamp.replace(hour=1, minute=0, second=0, microsecond=0)
    hour = datetime.timedelta(seconds=60*60)
    event = 'event_report_query_monthly_by_daily'
    with DBTest:
        Monthly.record(event, stamp)
        Monthly.record(event, stamp + hour)
        Monthly.record(event, stamp + hour + hour)

        counts = Monthly.daily(event)[-2:-1]
        eq_(counts, [3])
        count = counts[0]
        eq_(count.timestamp.timetuple()[:3], stamp.timetuple()[:3])
        eq_(count.hour, 0)


def test_report_query_monthly_by_hourly():
    stamp = pytool.time.utcnow()
    stamp = stamp.replace(hour=1, minute=0, second=0, microsecond=0)
    hour = datetime.timedelta(seconds=60*60)
    event = 'event_report_query_monthly_by_hourly'
    with DBTest:
        Monthly.record(event, stamp)
        Monthly.record(event, stamp + hour)
        Monthly.record(event, stamp + hour + hour)

        counts = Monthly.hourly(event)[stamp - hour:stamp + hour * 4]
        eq_(counts, [0, 1, 1, 1, 0])
        for count in counts:
            eq_(count.year, stamp.year)
            eq_(count.month, stamp.month)
            eq_(count.day, stamp.day)
            eq_(count.minute, 0)

        eq_([c.hour for c in counts], [0, 1, 2, 3, 4])


def test_report_query_yearly_by_monthly():
    stamp = pytool.time.utcnow()
    stamp = report._relative_period(YEAR, stamp, -1)
    stamp = stamp.replace(hour=1, minute=0, second=0, microsecond=0)
    hour = datetime.timedelta(seconds=60*60)
    event = 'event_report_query_yearly_by_monthly'
    with DBTest:
        Yearly.record(event, stamp)
        Yearly.record(event, stamp + hour)
        Yearly.record(event, stamp + hour + hour)

        counts = Yearly.monthly(event)[stamp - hour:stamp + hour]
        eq_(counts, [3])
        count = counts[0]
        eq_(count.timestamp.timetuple()[:2], stamp.timetuple()[:2])
        eq_(count.day, 1)
        eq_(count.hour, 0)


def test_report_query_regex():
    stamp = pytool.time.utcnow()
    stamp -= datetime.timedelta(days=1)
    stamp = stamp.replace(hour=1, minute=0, second=0, microsecond=0)
    hour = datetime.timedelta(seconds=60*60)
    with DBTest:
        Monthly.record('regex_test1', stamp)
        Monthly.record('regex_test2', stamp + hour)
        counts = Monthly.daily('regex_test', regex=True)[-2:-1]
        eq_(len(counts), 2)
        eq_(counts['regex_test1'], [1])
        eq_(counts['regex_test1'], [1])


def test_report_query_end_index():
    stamp = pytool.time.utcnow()
    this_year = stamp.year
    last_year = stamp.year-1

    stamp = datetime.datetime(this_year, 12, 31, 23, 59, 59,
            tzinfo=pytool.time.UTC())

    event = 'event_report_query_end_index'
    with DBTest:
        Daily.record(event, stamp, safe=True)
        eq_(Daily.yearly(event)[last_year+1:this_year+1][-1], 1)
        eq_(Daily.monthly(event)[1:13][-1], 1)

    stamp = pytool.time.utcnow()
    stamp = report._relative_period(MONTH, stamp, 1)
    stamp -= datetime.timedelta(seconds=1)
    event = 'event_report_query_end_index_daily'
    with DBTest:
        Daily.record(event, stamp)
        _, end_of_month = calendar.monthrange(stamp.year, stamp.month)
        eq_(Daily.daily(event)[1:end_of_month+1][-1], 1)

    stamp = pytool.time.utcnow()
    stamp = stamp.replace(hour=23, minute=59, second=59)
    event = 'event_report_query_end_index_daily_day'
    with DBTest:
        Daily.record(event, stamp)
        eq_(Daily.hourly(event)[0:24][-1], 1)

    stamp = pytool.time.utcnow()
    stamp = stamp.replace(minute=59, second=59)
    event = 'event_query_end_index_per_minute'
    with DBTest:
        Daily.record(event, stamp)
        eq_(Daily.per_minute(event)[0:60][-1], 1)


def test_unspecified_start_year_index():
    stamp = pytool.time.utcnow()
    this_year = stamp.year
    two_years_ago = this_year-2
    two_years_ago_stamp = stamp.replace(year=two_years_ago)
    diff = 0-(this_year-two_years_ago)
    event = 'event_unspecified_start_year_index'
    with DBTest:
        ByHour.record(event, two_years_ago_stamp)
        eq_(ByHour.yearly(event)[:-1][diff], 1)

def test_no_results():
    with DBTest:
        eq_(ByHour.hourly('None')[-1:], [])


@raises(IndexError)
def test_year_index_out_of_range():
    ByHour.yearly[:2038]


@raises(IndexError)
def test_year_index_out_of_range_lower():
    ByHour.yearly[1969:]


@raises(IndexError)
def test_month_index_out_of_range():
    ByHour.monthly[:14]


@raises(IndexError)
def test_month_index_out_of_range2():
    ByHour.monthly[0:]


@raises(IndexError)
def test_daily_index_out_of_range():
    ByHour.daily[:33]


@raises(IndexError)
def test_daily_index_out_of_range2():
    ByHour.daily[0:]


@raises(IndexError)
def test_hour_index_out_of_range():
    ByHour.hourly[:25]


@raises(IndexError)
def test_minute_index_out_of_range():
    Daily.per_minute[:61]


@raises(TypeError)
def test_bad_index_type():
    Daily.per_minute['foo']


@raises(TypeError)
def test_bad_index_type_slice():
    Daily.per_minute['foo':]


def test_report_count_addition_maintains_lesser_timestamp():
    stamp = pytool.time.utcnow()
    stamp2 = stamp + datetime.timedelta(seconds=1)
    a = report.ReportCount(3, stamp)
    b = report.ReportCount(5, stamp2)
    c = a + b
    eq_(c, 8)
    eq_(c.timestamp, stamp)


def test_report_count_works_with_integers():
    stamp = pytool.time.utcnow()
    a = report.ReportCount(3, stamp)
    b = a + 2
    eq_(b, 5)
    eq_(b.timestamp, stamp)
    c = b + 3
    eq_(c, 8)
    eq_(c.timestamp, stamp)
    c += 5
    eq_(c, 13)
    eq_(c.timestamp, stamp)


def test_report_query_coerces_date():
    stamp = pytool.time.utcnow()
    hour = datetime.timedelta(seconds=60*60)

    event = 'event_date_coercion'
    with DBTest:
        ByHour.record(event, pytool.time.floor_day(stamp) - hour)
        eq_(ByHour.daily(event)[-2:-1], [1])


def test_relative_period_MONTH_across_end_of_year_and_beginning():
    stamp = datetime.datetime(2013, 1, 1, tzinfo=pytool.time.UTC())
    eq_(report._relative_period(MONTH, stamp, -1), datetime.datetime(2012, 12,
        1, tzinfo=pytool.time.UTC()))

    stamp = datetime.datetime(2013, 12, 1, tzinfo=pytool.time.UTC())
    eq_(report._relative_period(MONTH, stamp, 1), datetime.datetime(2014, 1,
        1, tzinfo=pytool.time.UTC()))


def test_monthly_report_queried_daily_returns_correct_length():
    class Sum(Report):
        config_database = database_name()
        config_collection = 'report.sum'
        config_period = MONTH
        config_intervals = [MONTH, HOUR]

    now = pytool.time.utcnow()
    earlier = report._relative_period(MONTH, now, -1)

    event = 'monthly_as_daily'
    with DBTest:
        Sum.record(event)
        Sum.record(event, stamp=earlier)
        days = Sum.daily[-65:]

    days = days.get(event, [])
    # Check we get the right number of days
    eq_(len(days), 65)
    # Check we get the correct total
    eq_(sum(days), 2)

    # Ensure dates come back in correct order
    date = report._relative_period(DAY, days[0].timestamp, -1)
    for day in days:
        ok_(day.timestamp > date)
        date = day.timestamp


def test_report_queried_with_date_works():
    now = pytool.time.utcnow()
    today = now.date()
    tomorrow = now + datetime.timedelta(days=1)
    tomorrow = tomorrow.date()

    event = 'event_query_with_date'
    with DBTest:
        Monthly.record(event)
        Monthly.record(event)
        Monthly.record(event)
        eq_(sum(Monthly.daily(event)[today:tomorrow]), 3)


def test_record_arbitrary_count():
    event = 'event_arbitrary_count'
    with DBTest:
        Monthly.record(event, count=20)
        eq_(sum(Monthly.hourly(event)[-1:]), 20)


def test_record_negative_count():
    event = 'event_negative_count'
    with DBTest:
        Monthly.record(event, count=-5)
        eq_(sum(Monthly.hourly(event)[-1:]), -5)


@raises(ValueError)
def test_record_bad_stamp_type_raises_value_error():
    Monthly.record('foo', 20)


@raises(ValueError)
def test_record_bad_count_type_raises_value_error():
    Monthly.record('foo', count='bar')


@raises(ValueError)
def test_record_bad_count_type_raises_value_error2():
    Monthly.record('foo', count=2.5)


def test_recording_and_retrieving_in_september_works():
    with DBTest:
        Monthly.record('test_september', datetime.datetime(2013, 9, 1, 12))

    with DBTest:
        vals = Monthly.hourly('test_september')[datetime.datetime(2013, 8, 1):
                datetime.datetime(2013, 10, 10)]

    eq_(sum(vals), 1)

