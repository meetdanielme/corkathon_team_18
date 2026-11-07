from datetime import date, datetime

from footfall.domain.cutoffs import cutoff_for, serving_delivery
from footfall.domain.timeutil import TZ


def test_weekday_rule_saturday_delivery_cuts_off_thursday():
    rule = {"type": "weekday", "day": "thu", "time": "16:00"}
    assert cutoff_for(rule, date(2026, 11, 14)) == datetime(2026, 11, 12, 16, 0, tzinfo=TZ)


def test_business_days_skip_closed_sunday():
    rule = {"type": "business_days_before", "n": 2, "time": "16:00", "closed": ["sun"]}
    # Monday delivery: Sun closed, Sat counts 1, Fri counts 2 -> Fri, not Sat (naive 48h)
    assert cutoff_for(rule, date(2026, 11, 16)) == datetime(2026, 11, 13, 16, 0, tzinfo=TZ)


def test_business_days_skip_holiday():
    rule = {"type": "business_days_before", "n": 1, "time": "16:00", "closed": ["sun"]}
    assert cutoff_for(rule, date(2026, 11, 12), holidays=frozenset({date(2026, 11, 11)})) == \
        datetime(2026, 11, 10, 16, 0, tzinfo=TZ)


def test_serving_delivery_same_day_then_day_before():
    assert serving_delivery({"thu"}, date(2026, 11, 12)) == date(2026, 11, 12)
    assert serving_delivery({"wed"}, date(2026, 11, 12)) == date(2026, 11, 11)
    assert serving_delivery({"mon"}, date(2026, 11, 12)) is None
