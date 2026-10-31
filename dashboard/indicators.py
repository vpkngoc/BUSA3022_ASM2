"""Dashboard indicators (Part 3, v0 baseline).

Everything the dashboard shows is either a column of data/serve/daily_panel.csv (Part 2)
or one of the three indicators below. They are DRAFTS for the team's critique:

* volume_vs_normal_pct, rag_status: metric M4 as the team defined it in docs/METRICS.md v1.2
  (Green below +30%, Amber +30% to below +60%, Red +60% or more; the newest day is Pending
  until its volume is final; a zero-volume session is invalid and Excluded).
* corr20: rolling 20-session correlation of the daily ASX return with the same-day change
  in the RBA 10-year yield (the macro overlay). The same-day yield change is published days
  later, so this is a look-back measure, never something known that evening.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

WINDOW_DAYS = 90            # decision D7: 90 calendar days
NORMAL_SESSIONS = 20        # "normal" volume = average of the previous 20 final sessions
AMBER_AT = 0.30             # volume at least 30% above normal (METRICS.md M4)
RED_AT = 0.60               # ... at least 60% above normal
CORR_SESSIONS = 20
CORR_MIN = 15               # at least 15 paired days in the 20-session window


def window(panel: pd.DataFrame, days: int = WINDOW_DAYS) -> pd.DataFrame:
    """The last `days` calendar days, ending at the newest session."""
    end = date.fromisoformat(panel.trade_date_syd.max())
    start = (end - timedelta(days=days - 1)).isoformat()
    return panel[panel.trade_date_syd >= start].reset_index(drop=True)


def add_volume_vs_normal(panel: pd.DataFrame) -> pd.DataFrame:
    """Today's volume against the average of the previous 20 final, positive volumes.

    Only final bars count: a provisional or in-progress session has no volume yet, so its
    ratio is blank ("pending"), never zero. Zero volumes (e.g. 29 Jun 2026, DQ03) are not
    trading information and are left out of both the normal and the ratio.
    """
    out = panel.sort_values("trade_date_syd").reset_index(drop=True)
    vol = out["volume"].where((out["bar_status"] == "final") & (out["volume"] > 0))
    valid = vol.dropna()
    # mean of the last 20 valid volumes strictly before each session (also defined on pending days)
    rolled = valid.rolling(NORMAL_SESSIONS, min_periods=NORMAL_SESSIONS).mean().reindex(out.index)
    out["volume_normal"] = rolled.ffill().shift(1)
    out["volume_vs_normal_pct"] = (vol / out["volume_normal"] - 1) * 100
    return out


def add_rag(panel: pd.DataFrame) -> pd.DataFrame:
    """Green / Amber / Red / Pending / Excluded from volume_vs_normal_pct (METRICS.md M4 v1.2)."""
    out = panel.copy()
    r = out["volume_vs_normal_pct"] / 100
    excluded = (out["bar_status"] == "final") & ~(out["volume"] > 0)      # zero or missing final volume: invalid
    status = np.select([excluded, r.isna(), r >= RED_AT, r >= AMBER_AT],
                       ["Excluded", "Pending", "Red", "Amber"], "Green")
    out["rag_status"] = status
    return out


def add_corr20(panel: pd.DataFrame, f2: pd.DataFrame) -> pd.DataFrame:
    """Rolling correlation of daily ASX log return (%) with same-day yield change (bp)."""
    out = panel.sort_values("trade_date_syd").reset_index(drop=True)
    y = f2.dropna(subset=["value_pct"]).sort_values("trade_date_syd").set_index("trade_date_syd")["value_pct"]
    dy = (y.diff() * 100)
    close = out["close_pts"].where(out["bar_status"] != "in_progress")
    out["asx_return_pct"] = np.log(close / close.shift(1)) * 100
    out["yield_change_1d_bp"] = out["trade_date_syd"].map(dy)
    out["corr20"] = out["asx_return_pct"].rolling(CORR_SESSIONS, min_periods=CORR_MIN).corr(out["yield_change_1d_bp"])
    return out


def summary(w: pd.DataFrame, panel: pd.DataFrame) -> dict:
    """The numbers the headline, the RAG card and the tiles need."""
    last = w.iloc[-1]
    first = w.iloc[0]
    final = w[w.bar_status == "final"]
    lf = final.iloc[-1]
    year = panel[panel.trade_date_syd > (date.fromisoformat(last.trade_date_syd) - timedelta(days=365)).isoformat()]
    fired = w[w.rag_status.isin(["Amber", "Red"])]
    known = w.dropna(subset=["yield_same_day_pct"])
    return {
        "start": first.trade_date_syd, "end": last.trade_date_syd, "sessions": len(w),
        "end_status": last.bar_status, "review_time": last.review_time_syd,
        "close": last.close_pts, "close_change_pct": (last.close_pts / first.close_pts - 1) * 100,
        "ma20": last.ma20_pts, "close_vs_ma20_pct": (last.close_pts / last.ma20_pts - 1) * 100,
        "vol20": last.vol20_ann_pct, "vol20_1y_median": year.vol20_ann_pct.median(),
        "vol20_1y_p80": year.vol20_ann_pct.quantile(0.8),
        "yield_asat": last.yield_asat_pct, "yield_obs_date": last.yield_asat_obs_date,
        "yield_age": int(last.yield_asat_age_sessions), "yield_change_5obs_bp": last.yield_change_5obs_bp,
        "yield_asat_change_bp": (last.yield_asat_pct - first.yield_asat_pct) * 100,
        "last_rba_date": known.trade_date_syd.max() if len(known) else None,
        "rag_date": lf.trade_date_syd, "rag_status": lf.rag_status, "rag_pct": lf.volume_vs_normal_pct,
        "fired_amber": int((fired.rag_status == "Amber").sum()), "fired_red": int((fired.rag_status == "Red").sum()),
        "fired_dates": fired[["trade_date_syd", "rag_status", "volume_vs_normal_pct"]].to_dict("records"),
        "corr20": w.corr20.dropna().iloc[-1] if w.corr20.notna().any() else None,
        "corr20_min": w.corr20.min(), "corr20_max": w.corr20.max(),
    }
