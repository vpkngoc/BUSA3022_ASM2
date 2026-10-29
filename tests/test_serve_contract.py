"""Data modelling standards (CONTRIBUTING.md), enforced on the real serve table.

Built from the clean tables committed in data/curated, so CI checks the data the dashboard
will actually use, whoever (person or agent) wrote the code that produced it.
"""
import re
from datetime import datetime

import pandas as pd
import pytest

from pipeline import align
from pipeline.config import CURATED, SYD

UNIT_SUFFIXES = ("_pts", "_pct", "_bp", "_syd", "_utc", "_date", "_sessions", "_status", "_flags")
NO_UNIT = {"volume"}            # Yahoo index volume: relative use only (see docs/DATA_DICTIONARY.md)


def read(name):
    return pd.read_csv(CURATED / name, dtype={"dq_flags": str}, keep_default_na=False, na_values=[""])


@pytest.fixture(scope="module")
def panel():
    if not (CURATED / "asx200_daily.csv").exists():
        pytest.skip("no committed clean tables")
    return align.build_panel(read("asx200_daily.csv"), read("au10y_daily.csv"), read("au10y_vintages.csv"))


def test_names_are_snake_case_with_a_unit(panel):
    for c in panel.columns:
        assert re.fullmatch(r"[a-z][a-z0-9_]*", c), c
        assert c.endswith(UNIT_SUFFIXES) or c in NO_UNIT, f"{c} has no unit suffix"


def test_grain_is_one_row_per_sydney_trading_date(panel):
    assert panel.trade_date_syd.is_unique and panel.trade_date_syd.is_monotonic_increasing
    assert (pd.to_datetime(panel.trade_date_syd).dt.day_of_week < 5).all()


def test_review_times_carry_the_right_sydney_offset(panel):
    for d, t in zip(panel.trade_date_syd, panel.review_time_syd):
        expected = datetime.fromisoformat(f"{d}T18:00").replace(tzinfo=SYD).isoformat(timespec="minutes")
        assert t == expected


def test_no_look_ahead_and_no_filled_yields(panel):
    f2 = read("au10y_daily.csv").set_index("trade_date_syd")
    p = panel.dropna(subset=["yield_asat_obs_date"])
    assert (p.yield_asat_obs_date < p.trade_date_syd).all()
    known = panel.trade_date_syd.map(f2.value_pct)
    assert panel.yield_same_day_pct.isna().equals(known.isna())     # NULL exactly where the RBA has none
    flagged = panel.dq_flags.fillna("").str.contains("rba:DQ04")
    assert flagged.equals(panel.yield_same_day_pct.isna())          # ... and flagged exactly there (METRICS.md M3)
