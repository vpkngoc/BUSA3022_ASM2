"""Part 2: put both sources on one time axis and serve the metrics.

    python -m pipeline.align        # rebuild data/serve/daily_panel.csv from the clean tables

The axis is the ASX trading session, dated in Sydney. For each session the panel answers:
what did a manager at the 6:00 pm Sydney review on that day know?

* ASX close, 20-session average and volatility: known the same evening.
* The RBA yield "as at" the review: the newest RBA observation already published by
  6:00 pm Sydney that day (point in time, no look-ahead). It is usually 2 to 6 sessions old,
  because the RBA publishes F2 weekly. Its 5-observation change is calculated on the RBA's
  own dates first, then carried to the session (see pipeline.metrics).
* The RBA yield dated the same day: only known days later. Kept for analysis (for example a
  same-day correlation), never shown as if it had been known that evening.

The 6:00 pm review time is converted with the Australia/Sydney time zone rules for each
date, so it is 08:00 UTC in winter (AEST, UTC+10) and 07:00 UTC in summer (AEDT, UTC+11).
Nothing is forward-filled: a missing RBA date stays NULL in the same-day column.
"""
from __future__ import annotations

from bisect import bisect_right
from datetime import datetime, time

import pandas as pd

from .config import CURATED, SYD
from .metrics import add_ma20, add_vol20, add_yield_change_5obs

SERVE = CURATED.parent / "serve"
REVIEW_TIME = time(18, 0)          # the evening review, Sydney local time
FINAL_BAR_TIME = "10:00"           # Yahoo stamps each completed daily bar 10:00 Sydney
SESSION_COMPLETE_TIME = "16:15"    # after the ASX closing auction (about 4:10 pm Sydney)

COLUMNS = ["trade_date_syd", "review_time_syd", "bar_status", "close_pts", "volume", "ma20_pts",
           "vol20_ann_pct", "yield_asat_pct", "yield_asat_obs_date", "yield_asat_age_sessions",
           "yield_change_5obs_bp", "yield_same_day_pct", "dq_flags"]


def review_instant(trade_date: str) -> datetime:
    """6:00 pm Sydney on a session date, as a time-zone-aware instant (DST handled by zoneinfo)."""
    return datetime.combine(datetime.strptime(trade_date, "%Y-%m-%d").date(), REVIEW_TIME, SYD)


def mark_provisional(asx: pd.DataFrame) -> pd.DataFrame:
    """Label each bar final, provisional or in_progress (data quality issue, Part 2).

    Yahoo stamps a completed daily bar 10:00 Sydney. The newest session usually arrives as a
    live bar instead, stamped with the time of its last update and with volume 0:
    * stamped after the closing auction (from 4:15 pm): provisional. The close stands, but the
      volume is not yet known, so it is NULL rather than zero. The next run replaces the bar,
      and any change to the close is logged as DQ08.
    * stamped during trading hours (a run started before the close): in_progress. The session
      is not completed, so it is kept for display but left out of every metric.
    """
    out = asx.copy()
    local = pd.to_datetime(out["observed_at_utc"], utc=True).dt.tz_convert(SYD).dt.strftime("%H:%M")
    out["bar_status"] = "provisional"
    out.loc[local == FINAL_BAR_TIME, "bar_status"] = "final"
    out.loc[(local != FINAL_BAR_TIME) & (local < SESSION_COMPLETE_TIME), "bar_status"] = "in_progress"
    out["volume"] = out["volume"].astype("Float64").mask(out["bar_status"] != "final")
    return out


def first_available(f2: pd.DataFrame, vintages: pd.DataFrame | None) -> pd.Series:
    """When each RBA date's value was first published (earliest vintage), as UTC instants."""
    src = vintages if vintages is not None and len(vintages) else f2
    first = (src.dropna(subset=["available_from_syd"])
             .assign(t=lambda d: pd.to_datetime(d["available_from_syd"].map(datetime.fromisoformat), utc=True))
             .groupby("trade_date_syd")["t"].min())
    return f2["trade_date_syd"].map(first)


def build_panel(asx: pd.DataFrame, f2: pd.DataFrame, vintages: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per ASX session (Sydney date) with the three metrics and the yield 'as at' 6 pm."""
    a = mark_provisional(asx.sort_values("trade_date_syd"))
    a["_metric_close"] = a["close"].mask(a["bar_status"] == "in_progress")   # completed sessions only
    a = add_vol20(add_ma20(a, "_metric_close"), "_metric_close").rename(columns={"close": "close_pts"})
    a["review_time_syd"] = a["trade_date_syd"].map(lambda d: review_instant(d).isoformat(timespec="minutes"))
    a["_review_utc"] = pd.to_datetime(a["trade_date_syd"].map(review_instant), utc=True)

    y = add_yield_change_5obs(f2.sort_values("trade_date_syd"))
    y["_avail_utc"] = first_available(y, vintages)
    known = y[y["value_pct"].notna() & y["_avail_utc"].notna()].sort_values(["_avail_utc", "trade_date_syd"])
    # newest RBA date published by each availability instant (robust to out-of-order revisions)
    known = known.assign(_newest=known["trade_date_syd"].cummax())[["_avail_utc", "_newest"]]

    a = pd.merge_asof(a.sort_values("_review_utc"), known, left_on="_review_utc", right_on="_avail_utc",
                      direction="backward")
    by_date = y.set_index("trade_date_syd")
    a["yield_asat_obs_date"] = a["_newest"]
    a["yield_asat_pct"] = a["_newest"].map(by_date["value_pct"])
    a["yield_change_5obs_bp"] = a["_newest"].map(by_date["yield_change_5obs_bp"])
    a["yield_same_day_pct"] = a["trade_date_syd"].map(by_date["value_pct"])   # NULL if the RBA has no value

    # age = ASX sessions after the RBA date, up to and including this session (Fri 2 ... Thu 6);
    # NULL when the RBA date is older than the ASX history, so the sessions cannot be counted
    sessions = sorted(a["trade_date_syd"])
    a["yield_asat_age_sessions"] = pd.array(
        [pd.NA if pd.isna(obs) or obs < sessions[0] else bisect_right(sessions, d) - bisect_right(sessions, obs)
         for d, obs in zip(a["trade_date_syd"], a["yield_asat_obs_date"])], dtype="Int64")

    def tag(prefix, flags):
        return flags.fillna("").map(lambda f: ";".join(f"{prefix}:{x}" for x in str(f).split(";") if x))
    # METRICS.md (M3): an ASX day with no RBA observation keeps a missing yield AND is flagged.
    # DQ04 covers both a blank RBA date (e.g. Labour Day) and a date the RBA has not published yet.
    rba = a["trade_date_syd"].map(by_date["dq_flags"]).fillna("").astype(str)
    no_yield = a["yield_same_day_pct"].isna()
    rba = [f if not missing or "DQ04" in f.split(";") else ";".join(x for x in (f, "DQ04") if x)
           for f, missing in zip(rba, no_yield)]
    a["dq_flags"] = [";".join(x for x in pair if x) for pair in
                     zip(tag("asx", a["dq_flags"]), tag("rba", pd.Series(rba, index=a.index)))]
    return a[COLUMNS].sort_values("trade_date_syd").reset_index(drop=True)


def _read(name: str) -> pd.DataFrame | None:
    path = CURATED / name
    return pd.read_csv(path, dtype={"dq_flags": str}, keep_default_na=False, na_values=[""]) if path.exists() else None


def rebuild() -> dict:
    """Rebuild the serve table from the clean tables and return a one-line summary."""
    asx, f2 = _read("asx200_daily.csv"), _read("au10y_daily.csv")
    if asx is None or f2 is None:
        raise FileNotFoundError("clean tables missing: run python -m pipeline.run first")
    panel = build_panel(asx, f2, _read("au10y_vintages.csv"))
    SERVE.mkdir(parents=True, exist_ok=True)
    panel.to_csv(SERVE / "daily_panel.csv", index=False)
    last = panel.iloc[-1]
    return {"sessions": len(panel), "latest_session": last.trade_date_syd, "bar_status": last.bar_status,
            "yield_asat_obs_date": last.yield_asat_obs_date, "yield_asat_age_sessions": last.yield_asat_age_sessions}


if __name__ == "__main__":
    print(rebuild())
