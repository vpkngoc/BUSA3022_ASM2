"""Dashboard indicators (Part 3 v0): the draft volume signal, the window and the overlay."""
import pandas as pd
import pytest

from dashboard import build, indicators as ind
from pipeline.config import CURATED


def sessions(vols, status=None):
    d = pd.bdate_range("2026-06-01", periods=len(vols)).strftime("%Y-%m-%d")
    return pd.DataFrame({"trade_date_syd": d, "volume": vols, "bar_status": status or ["final"] * len(vols)})


def test_normal_is_the_previous_20_final_volumes():
    out = ind.add_volume_vs_normal(sessions([100.0] * 20 + [130.0]))
    assert out.volume_vs_normal_pct.iloc[:20].isna().all()          # no normal before 20 sessions
    assert out.volume_vs_normal_pct.iloc[20] == pytest.approx(30.0)


def test_zero_volume_is_excluded_and_unfinished_is_pending():
    status = ["final"] * 21 + ["provisional"]
    out = ind.add_rag(ind.add_volume_vs_normal(sessions([100.0] * 10 + [0.0] + [100.0] * 10 + [None], status)))
    assert out.volume_normal.iloc[-1] == pytest.approx(100.0)        # the zero day is not part of the normal
    assert out.rag_status.iloc[10] == "Excluded"                       # M4 v1.2: invalid, not a quiet day
    assert out.rag_status.iloc[-1] == "Pending"                        # newest day not final yet


@pytest.mark.parametrize("today, expected", [(129.0, "Green"), (130.0, "Amber"), (159.0, "Amber"), (160.0, "Red")])
def test_thresholds(today, expected):
    out = ind.add_rag(ind.add_volume_vs_normal(sessions([100.0] * 20 + [today])))
    assert out.rag_status.iloc[-1] == expected


def test_three_amber_sessions_in_a_row_stay_amber():
    """M4 v1.2 has no run rule: Red is +60% or more only (v0's draft run rule was dropped)."""
    vols = [100.0] * 20 + [140.0, 150.0, 160.0]                       # each about 35-45% above its normal
    out = ind.add_rag(ind.add_volume_vs_normal(sessions(vols)))
    assert list(out.rag_status.iloc[-3:]) == ["Amber", "Amber", "Amber"]


def test_window_is_90_calendar_days_ending_at_the_newest_session():
    p = pd.DataFrame({"trade_date_syd": pd.bdate_range("2026-01-01", "2026-10-29").strftime("%Y-%m-%d")})
    w = ind.window(p)
    assert w.trade_date_syd.max() == "2026-10-29" and w.trade_date_syd.min() >= "2026-08-01"


def test_the_page_builds_from_the_committed_data():
    if not (CURATED.parent / "serve" / "daily_panel.csv").exists():
        pytest.skip("no serve table committed yet")
    m = build.model(build._read(build.SERVE), build._read(CURATED / "au10y_daily.csv"))
    html = build.render(m)
    assert m["summary_90d"]["sessions"] > 50 and "/*__DATA__*/" not in html
    assert m["default_days"] == 90                                     # the brief's 90 days is the default range
    assert len(m["rows"]) > 200                                        # one year of sessions for the 1Y button
    assert all(r["volume"] is None for r in m["rows"] if r["bar_status"] != "final")   # never a fake zero


def test_last_fetch_ignores_simulated_runs(tmp_path):
    log = tmp_path / "log.csv"
    log.write_text("run_at_utc,simulated\n2026-10-29T14:25:14Z,False\n2026-10-30T02:00:00Z,True\n")
    assert build.last_fetch(log) == "Fri 30 Oct 2026, 01:25 Sydney"
