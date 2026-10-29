"""Part 2 metrics, implemented exactly as the team defined them in docs/METRICS.md.

Each function takes one source's clean table and adds one column. Nothing is filled in:
a metric is NULL until its window holds enough valid observations.

| Column | Function | Window |
| --- | --- | --- |
| ma20_pts | add_ma20 | 20 valid ASX closes |
| vol20_ann_pct | add_vol20 | 20 daily log returns, i.e. 21 valid closes |
| yield_change_5obs_bp | add_yield_change_5obs | the 5th previous valid RBA observation |
"""
from __future__ import annotations

import numpy as np
import pandas as pd

WINDOW = 20             # completed ASX trading sessions
TRADING_DAYS = 252      # annualisation convention for daily volatility
YIELD_LAG_OBS = 5       # valid RBA observations, about one business week


def _valid(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    """Rows with a value, in date order. Missing values are skipped, never filled."""
    return df[df[value_col].notna()].sort_values(date_col)


def add_ma20(asx: pd.DataFrame, close_col: str = "close") -> pd.DataFrame:
    """MA20_t = (1/20) * sum of the latest 20 valid closes. NULL until 20 valid closes exist."""
    out = asx.reset_index(drop=True)
    v = _valid(out, "trade_date_syd", close_col)
    out["ma20_pts"] = v[close_col].rolling(WINDOW, min_periods=WINDOW).mean()
    return out


def add_vol20(asx: pd.DataFrame, close_col: str = "close") -> pd.DataFrame:
    """Vol20_t = sample sd of the latest 20 daily log returns x sqrt(252) x 100.

    r_t = ln(P_t / P_t-1) between consecutive valid closes. Twenty returns need 21 closes,
    so the first 20 sessions are NULL. The standard deviation is the sample one (n - 1).
    """
    out = asx.reset_index(drop=True)
    v = _valid(out, "trade_date_syd", close_col)
    r = np.log(v[close_col] / v[close_col].shift(1))
    out["vol20_ann_pct"] = r.rolling(WINDOW, min_periods=WINDOW).std(ddof=1) * np.sqrt(TRADING_DAYS) * 100
    return out


def add_yield_change_5obs(f2: pd.DataFrame, value_col: str = "value_pct") -> pd.DataFrame:
    """Change from the 5th previous valid RBA observation, in basis points.

    Calculated on the RBA's own dates, before any join to ASX dates, so a blank RBA date
    (for example NSW Labour Day) is skipped rather than treated as a zero change. Rounded to
    0.1 bp, the precision of the source (yields are published to three decimal places).
    Blank dates keep a NULL change.
    """
    out = f2.reset_index(drop=True)
    v = _valid(out, "trade_date_syd", value_col)
    out["yield_change_5obs_bp"] = ((v[value_col] - v[value_col].shift(YIELD_LAG_OBS)) * 100).round(1)
    return out
