"""The Sydney time axis: what a manager could know at 6 pm on each ASX session.

Synthetic data built on the RBA release rule (weekly, Friday 2:00 pm, covering up to two
business days earlier). Dates are chosen away from the team's hand-checked edge dates.
"""
from datetime import date, datetime

import pandas as pd
import pytest

from pipeline import align, store
from pipeline.config import SYD
from pipeline.release_calendar import release_covering


def make(start="2026-06-01", end="2026-07-31", blank=(), release_time=None):
    days = pd.bdate_range(start, end).strftime("%Y-%m-%d").tolist()
    asx = pd.DataFrame({"trade_date_syd": days,
                        "observed_at_utc": [f"{d}T00:00:00Z" for d in days],   # 10:00 Sydney in winter
                        "close": [8000.0 + i for i in range(len(days))], "volume": 1000, "dq_flags": None})
    f2 = pd.DataFrame({"trade_date_syd": days, "value_pct": [None if d in blank else 4.0 + i / 1000
                                                              for i, d in enumerate(days)], "dq_flags": None})

    def avail(d):
        t = release_covering(date.fromisoformat(d))
        return (t.replace(hour=release_time) if release_time else t).isoformat(timespec="minutes")
    f2["available_from_syd"] = f2.trade_date_syd.map(avail)
    return asx, f2


def row(panel, d):
    return panel.set_index("trade_date_syd").loc[d]


def test_friday_review_sees_that_afternoons_release():
    p = align.build_panel(*make())
    fri = row(p, "2026-06-26")                       # release 2:00 pm covers through Wed 24 Jun
    assert fri.yield_asat_obs_date == "2026-06-24" and fri.yield_asat_age_sessions == 2
    thu = row(p, "2026-06-25")                       # still the previous week's release
    assert thu.yield_asat_obs_date == "2026-06-17" and thu.yield_asat_age_sessions == 6


def test_a_release_after_the_review_is_not_seen_that_evening():
    p = align.build_panel(*make(release_time=19))    # published 7 pm, after the 6 pm review
    assert row(p, "2026-06-26").yield_asat_obs_date == "2026-06-17"
    assert row(p, "2026-06-29").yield_asat_obs_date == "2026-06-24"


def test_no_session_ever_uses_a_yield_published_after_its_review():
    asx, f2 = make("2026-01-05", "2026-12-18")
    p = align.build_panel(asx, f2)
    avail = f2.set_index("trade_date_syd").available_from_syd.map(datetime.fromisoformat)
    for r in p.dropna(subset=["yield_asat_obs_date"]).itertuples():
        assert avail[r.yield_asat_obs_date] <= datetime.fromisoformat(r.review_time_syd)
        assert r.yield_asat_obs_date < r.trade_date_syd


@pytest.mark.parametrize("d, offset", [("2026-06-15", "+10:00"), ("2026-12-14", "+11:00")])
def test_review_time_carries_the_sydney_offset_for_that_date(d, offset):
    assert align.review_instant(d).isoformat(timespec="minutes") == f"{d}T18:00{offset}"


def test_a_blank_rba_date_is_never_filled():
    p = align.build_panel(*make(blank=("2026-07-15",)))
    wed = row(p, "2026-07-15")
    assert pd.isna(wed.yield_same_day_pct) and wed.dq_flags == "rba:DQ04"   # missing AND flagged
    assert row(p, "2026-07-16").yield_same_day_pct == pytest.approx(4.0 + 33 / 1000)


def test_live_bar_is_provisional_and_its_volume_unknown():
    asx, f2 = make()
    asx.loc[asx.index[-1], ["observed_at_utc", "volume"]] = ["2026-07-31T06:54:00Z", 0]   # 4:54 pm Sydney
    p = align.build_panel(asx, f2)
    assert p.bar_status.iloc[-1] == "provisional" and pd.isna(p.volume.iloc[-1])
    assert p.close_pts.iloc[-1] == asx.close.iloc[-1]           # the close is kept
    assert (p.bar_status.iloc[:-1] == "final").all()


def test_a_session_still_trading_is_shown_but_left_out_of_the_metrics():
    asx, f2 = make()
    before = align.build_panel(asx, f2)
    asx.loc[asx.index[-1], ["observed_at_utc", "volume", "close"]] = ["2026-07-31T02:20:00Z", 0, 9999.0]  # 12:20 pm
    p = align.build_panel(asx, f2)
    assert p.bar_status.iloc[-1] == "in_progress" and p.close_pts.iloc[-1] == 9999.0
    assert p[["ma20_pts", "vol20_ann_pct"]].iloc[-1].isna().all()
    pd.testing.assert_frame_equal(p.iloc[:-1], before.iloc[:-1])     # earlier sessions unaffected


# ------------------------------------------------------------------ storage changes for Part 2

@pytest.fixture
def curated(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "CURATED", tmp_path)
    return tmp_path


def test_replacing_a_provisional_bar_logs_a_changed_close(curated):
    asx, _ = make()
    store.upsert_asx(asx.tail(3), "r1")
    final = asx.tail(1).assign(close=asx.close.iloc[-1] + 2.5)
    _, revisions = store.upsert_asx(final, "r2")
    assert revisions.to_dict("records") == [{"trade_date_syd": "2026-07-31", "old_close": 8044.0,
                                             "new_close": 8046.5}]
    _, none = store.upsert_asx(final, "r3")
    assert none.empty


def test_new_yields_are_available_from_publication_not_download_time(curated):
    first = pd.DataFrame({"trade_date_syd": ["2026-10-21"], "value_pct": [5.277], "dq_flags": [""]})
    store.upsert_f2(first, "r1", datetime(2026, 10, 25, 17, 44, tzinfo=SYD))
    week2 = pd.concat([first, pd.DataFrame({"trade_date_syd": ["2026-10-28"], "value_pct": [5.3], "dq_flags": [""]})])
    late_run = datetime(2026, 10, 31, 1, 5, tzinfo=SYD)            # the scheduled run started after midnight
    merged, _ = store.upsert_f2(week2, "r2", late_run, "30-Oct-2026")
    assert merged.set_index("trade_date_syd").available_from_syd["2026-10-28"] == "2026-10-30T14:00+11:00"
