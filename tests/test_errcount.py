from __future__ import annotations

import datetime
import operator
import time
from typing import Any

import pytest
from zabbix_auto_config.errcount import Error
from zabbix_auto_config.errcount import RollingErrorCounter
from zabbix_auto_config.errcount import get_td


def test_get_td():
    """Sanity test that the get_td() helper function works as we expect."""
    td = get_td(60)
    assert td.total_seconds() == 60


def test_rolling_error_counter_init():
    """Test that we can create a RollingErrorCounter object."""
    rec = RollingErrorCounter(60, 5)
    assert rec.duration == 60
    assert rec.tolerance == 5
    assert rec.errors == []


def test_rolling_error_counter_init_negative_duration():
    """Test that we can't create a RollingErrorCounter object with a negative duration."""
    with pytest.raises(ValueError) as exc_info:
        RollingErrorCounter(-60, 5)
    assert "duration" in str(exc_info.value)


def test_rolling_error_counter_init_negative_tolerance():
    """Test that we can't create a RollingErrorCounter object with a negative tolerance."""
    with pytest.raises(ValueError) as exc_info:
        RollingErrorCounter(60, -5)
    assert "tolerance" in str(exc_info.value)


def test_rolling_error_counter_add():
    """Test that we can add errors to the RollingErrorCounter object."""
    rec = RollingErrorCounter(60, 5)
    rec.add()
    assert len(rec.errors) == 1
    time.sleep(0.01)  # ensure that the timestamp is always different
    rec.add()
    assert len(rec.errors) == 2
    assert rec.errors[0] < rec.errors[1]


def test_rolling_error_counter_count():
    """Test that we can count errors in the RollingErrorCounter object."""
    rec = RollingErrorCounter(0.03, 5)
    # This test is a bit timing sensitive, but we should be able to
    assert rec.count() == 0
    rec.add()
    assert rec.count() == 1
    rec.add()
    assert rec.count() == 2
    rec.add()
    assert rec.count() == 3
    rec.add()
    assert rec.count() == 4
    time.sleep(0.03)  # enough to reset the counter
    assert rec.count() == 0


def test_rolling_error_counter_count_is_rolling():
    """Check that the error counter is actually rolling by incrementally adding
    and sleeping. At some point we should see the counter decrease because
    an entry has expired."""
    # Init an error counter that rolls every 0.05 seconds.
    # Trying to use a shorter interval, such as 0.01, is flaky in CI.
    # We add 2 errors, then sleep 0.1 seconds to ensure the they have expired
    # before we add a new one and check the count.
    rec = RollingErrorCounter(0.05, 5)
    rec.add()
    rec.add()
    assert rec.count() == 2
    time.sleep(0.1)  # Double duration just to be sure the first two expired
    rec.add()
    assert rec.count() == 1


def test_rolling_error_counter_tolerance_exceeded():
    """Check that tolerance_exceeded() returns True when the tolerance is exceeded."""
    rec = RollingErrorCounter(60, 5)
    assert not rec.tolerance_exceeded()
    for _ in range(6):  # tolerance + 1
        rec.add()
    assert rec.count() == 6
    assert rec.tolerance_exceeded()

    # Resetting the counter should should make the check pass
    rec.reset()
    assert not rec.tolerance_exceeded()


def test_rolling_error_counter_tolerance_exceeded_0():
    """Test tolerance_exceeded with a 0 tolerance."""
    rec = RollingErrorCounter(60, 0)
    assert rec.count() == 0
    assert not rec.tolerance_exceeded()
    rec.add()
    assert rec.count() == 1
    assert rec.tolerance_exceeded()


def test_error_comparison():
    err1 = Error(timestamp=datetime.datetime(2020, 1, 1, 0, 0, 0))
    err2 = Error(timestamp=datetime.datetime(2021, 1, 1, 0, 0, 0))

    assert err1 < err2
    assert err2 > err1
    assert err1 <= err2
    assert err2 >= err1
    assert err1 != err2
    assert err1 == err1
    assert err2 == err2


@pytest.mark.parametrize(
    "op",
    [
        pytest.param(operator.eq, id="eq"),
        pytest.param(operator.ne, id="ne"),
        pytest.param(
            operator.lt, marks=pytest.mark.xfail(raises=TypeError, strict=True), id="lt"
        ),
        pytest.param(
            operator.le, marks=pytest.mark.xfail(raises=TypeError, strict=True), id="le"
        ),
        pytest.param(
            operator.ge, marks=pytest.mark.xfail(raises=TypeError, strict=True), id="ge"
        ),
        pytest.param(
            operator.gt, marks=pytest.mark.xfail(raises=TypeError, strict=True), id="gt"
        ),
    ],
)
def test_error_comparison_non_error(op: Any) -> None:
    """Comparison of Error with non-Error."""
    e = Error(timestamp=datetime.datetime(2020, 1, 1, 0, 0, 0))

    op(e, "foo")
    op(e, 1)
