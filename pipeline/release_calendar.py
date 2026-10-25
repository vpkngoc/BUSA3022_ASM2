"""The RBA's publication clock for Table F2.

F2 is released weekly on Fridays at 2:00 pm Sydney time, covering daily yields up to two
business days earlier (RBA, Frequency of statistical releases). Business days here are
Monday to Friday; public holidays are not modelled, which is a stated simplification.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pandas as pd

from .config import SYD

RELEASE_WEEKDAY = 4  # Friday
RELEASE_TIME = time(14, 0)


def latest_release_date(as_of: datetime) -> date:
    """Date of the most recent F2 release at or before `as_of` (tz-aware)."""
    local = as_of.astimezone(SYD)
    d = local.date()
    days_back = (d.weekday() - RELEASE_WEEKDAY) % 7
    friday = d - timedelta(days=days_back)
    if days_back == 0 and local.time() < RELEASE_TIME:
        friday -= timedelta(days=7)
    return friday


def expected_through(as_of: datetime) -> date:
    """Latest yield date that should be published at `as_of`."""
    return (pd.Timestamp(latest_release_date(as_of)) - pd.offsets.BDay(2)).date()


def release_covering(d: date) -> datetime:
    """When a yield for business date `d` is first published (used to reconstruct availability)."""
    friday = d + timedelta(days=(RELEASE_WEEKDAY - d.weekday()) % 7)
    while (pd.Timestamp(friday) - pd.offsets.BDay(2)).date() < d:
        friday += timedelta(days=7)
    return datetime.combine(friday, RELEASE_TIME, SYD)
