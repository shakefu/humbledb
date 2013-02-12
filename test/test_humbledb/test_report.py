import pytool

from ..util import *
from humbledb.report import (DailyReport, WeeklyReport, MonthlyReport,
        ReportBase)


def teardown():
    DBTest.connection.drop_database(database_name())


@raises(NotImplementedError)
def test_bad_subclass_raises_error():
    class BadReport(ReportBase):
        def get_id(self, event):
            return None

    BadReport().record('test')


@raises(NotImplementedError)
def test_other_bad_subclass_raises_error():
    class BadReport(ReportBase):
        def floor_date(self, stamp):
            return None

    BadReport().record('test')


@raises(NotImplementedError)
def test_other_bad_subclass_raises_error():
    class BadReport(ReportBase):
        def get_id(self, event):
            return ''

        def floor_date(self, stamp):
            import pytool
            return pytool.time.floor_day()

    BadReport().record('test')


class DailyReportTest(DailyReport):
    config_database = database_name()
    config_collection = 'report.day'


class WeeklyReportTest(WeeklyReport):
    config_database = database_name()
    config_collection = 'report.week'


class MonthlyReportTest(MonthlyReport):
    config_database = database_name()
    config_collection = 'report.month'


@raises(RuntimeError)
def test_daily_report_record_requires_mongo_context():
    DailyReportTest().record('test')


@raises(RuntimeError)
def test_weekly_report_record_requires_mongo_context():
    WeeklyReportTest().record('test')


@raises(RuntimeError)
def test_monthly_report_record_requires_mongo_context():
    MonthlyReportTest().record('test')


def test_daily_report_upserts_document():
    with DBTest:
        DailyReportTest.remove(safe=True)
        eq_(DailyReportTest.find().count(), 0)

        # We have to use safe writes here to ensure consistency when using a
        # sharded test environment
        DailyReportTest().record('test', safe=True)
        eq_(DailyReportTest.find().count(), 1)


def test_weekly_report_upserts_document():
    with DBTest:
        WeeklyReportTest.remove(safe=True)
        eq_(WeeklyReportTest.find().count(), 0)

        # We have to use safe writes here to ensure consistency when using a
        # sharded test environment
        WeeklyReportTest().record('test', safe=True)
        eq_(WeeklyReportTest.find().count(), 1)


def test_monthly_report_upserts_document():
    with DBTest:
        MonthlyReportTest.remove(safe=True)
        eq_(MonthlyReportTest.find().count(), 0)

        # We have to use safe writes here to ensure consistency when using a
        # sharded test environment
        MonthlyReportTest().record('test', safe=True)
        eq_(MonthlyReportTest.find().count(), 1)


def test_daily_report_has_correct_metadata():
    now = pytool.time.utcnow()
    with DBTest:
        DailyReportTest().record('test2', stamp=now, safe=True)

        r = DailyReportTest.find_one({DailyReportTest.meta.event: 'test2'})
        eq_(r.meta.event, 'test2')
        eq_(r.meta.date, pytool.time.floor_day(now))
