"""Ngoc's hand-worked check of the Sydney time axis (Part 2: date and time zone handling).

For each edge date I worked out by hand, from the RBA release rule (weekly, Friday 2:00 pm,
data up to two business days earlier), a calendar and the daylight-saving dates, what a
manager could know at the 6:00 pm Sydney review. Reasoning is in the pull request.
If the agent's join disagrees with the hand answer, this test fails.
"""
import pandas as pd
import pytest

from pipeline import align
from pipeline.config import CURATED

# date: (UTC offset at 6 pm, newest RBA date published by 6 pm, its age in ASX sessions,
#        does the RBA have a yield for this same date?)
MY_ANSWERS = {
    "2026-10-02": ("+10:00", "2026-09-30", 2, True),    # Fri: still AEST (DST starts Sun 4 Oct); 2 pm release covers to Wed 30 Sep
    "2026-10-05": ("+11:00", "2026-09-30", 3, False),   # Labour Day: ASX open, RBA blank; first Monday on AEDT
    "2026-10-06": ("+11:00", "2026-09-30", 4, True),    # no new release since Fri 2 Oct
    "2026-04-07": ("+10:00", "2026-04-01", 2, True),    # AEST (DST ended Sun 5 Apr); sessions after 1 Apr: Thu 2, Tue 7
}
# example of the format only: "2026-01-01": ("+11:00", "2025-12-29", 3, True)


def read(name):
    return pd.read_csv(CURATED / name, dtype={"dq_flags": str}, keep_default_na=False, na_values=[""])


@pytest.fixture(scope="module")
def panel():
    return align.build_panel(read("asx200_daily.csv"), read("au10y_daily.csv"),
                             read("au10y_vintages.csv")).set_index("trade_date_syd")


@pytest.mark.parametrize("d", MY_ANSWERS)
def test_edge_date_matches_my_hand_answer(panel, d):
    offset, obs_date, age, same_day = MY_ANSWERS[d]
    if None in (offset, obs_date, age, same_day):
        pytest.fail(f"type your hand answer for {d} first")
    row = panel.loc[d]
    assert row.review_time_syd.endswith(offset)
    assert row.yield_asat_obs_date == obs_date
    assert row.yield_asat_age_sessions == age
    assert pd.notna(row.yield_same_day_pct) == same_day