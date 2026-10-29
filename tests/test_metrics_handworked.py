"""Maika's hand-worked check of the three metrics (Part 2, AI Agent lens: Verify).

The expected numbers below were calculated by hand in Excel from data/curated/, BEFORE
looking at the pipeline's output (workbook: docs/evidence/part2_handcheck.xlsx).
If the agent's code disagrees with the hand calculation, this test fails.
"""
import pandas as pd
import pytest

from pipeline.config import CURATED
from pipeline.metrics import add_ma20, add_vol20, add_yield_change_5obs

ASX_DATE = "2026-10-23"     # the ASX session I checked
RBA_DATE = "2026-10-21"     # the RBA date I checked

# ---- my Excel results (type the numbers exactly as Excel shows them, 2 decimals is enough)
MY_MA20_PTS = 8745.29                 # =AVERAGE(20 closes ending on ASX_DATE)
MY_VOL20_ANN_PCT = 11.13798            # =STDEV.S(20 log returns ending on ASX_DATE)*SQRT(252)*100
MY_YIELD_CHANGE_5OBS_BP = -3.60     # =(gityield on RBA_DATE - yield 5 valid rows earlier)*100


def read(name):
    return pd.read_csv(CURATED / name, dtype={"dq_flags": str}, keep_default_na=False, na_values=[""])


def mine(value):
    if value is None:
        pytest.fail("type your Excel result into this file first")
    return value


def test_ma20_matches_my_excel():
    asx = add_ma20(read("asx200_daily.csv")).set_index("trade_date_syd")
    assert asx.loc[ASX_DATE, "ma20_pts"] == pytest.approx(mine(MY_MA20_PTS), abs=0.01)


def test_vol20_matches_my_excel():
    asx = add_vol20(read("asx200_daily.csv")).set_index("trade_date_syd")
    assert asx.loc[ASX_DATE, "vol20_ann_pct"] == pytest.approx(mine(MY_VOL20_ANN_PCT), abs=0.01)


def test_yield_change_matches_my_excel():
    f2 = add_yield_change_5obs(read("au10y_daily.csv")).set_index("trade_date_syd")
    assert f2.loc[RBA_DATE, "yield_change_5obs_bp"] == pytest.approx(mine(MY_YIELD_CHANGE_5OBS_BP), abs=0.05)