"""The three metrics in docs/METRICS.md, checked against independent calculations.

Expected values are computed with the standard library (math, statistics), not pandas,
so a mistake in the pandas code cannot also be in the expected answer.
"""
import math
import random
import statistics

import pandas as pd
import pytest

from pipeline.metrics import add_ma20, add_vol20, add_yield_change_5obs


def sessions(closes):
    dates = pd.bdate_range("2026-01-05", periods=len(closes)).strftime("%Y-%m-%d")
    return pd.DataFrame({"trade_date_syd": dates, "close": closes})


def test_ma20_is_null_until_20_closes_then_the_plain_average():
    out = add_ma20(sessions([float(x) for x in range(1, 26)]))
    assert out.ma20_pts.iloc[:19].isna().all()
    assert out.ma20_pts.iloc[19] == pytest.approx(10.5)          # mean of 1..20
    assert out.ma20_pts.iloc[24] == pytest.approx(15.5)          # mean of 6..25


def test_vol20_needs_21_closes_and_matches_a_hand_formula():
    random.seed(3)
    closes = [8000.0]
    for _ in range(30):
        closes.append(closes[-1] * math.exp(random.gauss(0, 0.007)))
    out = add_vol20(sessions(closes))
    assert out.vol20_ann_pct.iloc[:20].isna().all()              # 20 returns need 21 closes
    for t in (20, 30):
        returns = [math.log(closes[i] / closes[i - 1]) for i in range(t - 19, t + 1)]
        expected = statistics.stdev(returns) * math.sqrt(252) * 100   # sample sd (n - 1)
        assert out.vol20_ann_pct.iloc[t] == pytest.approx(expected, rel=1e-12)


def test_vol20_of_a_steady_trend_is_zero():
    closes = [100 * 1.001 ** i for i in range(25)]                # identical daily returns
    assert add_vol20(sessions(closes)).vol20_ann_pct.iloc[-1] == pytest.approx(0, abs=1e-9)


def test_a_missing_close_is_skipped_not_filled():
    closes = [float(x) for x in range(1, 22)]
    df = sessions(closes)
    df.loc[5, "close"] = None                                      # 20 valid closes remain
    out = add_ma20(df)
    assert pd.isna(out.ma20_pts.iloc[5])
    assert out.ma20_pts.iloc[-1] == pytest.approx(statistics.mean(c for i, c in enumerate(closes) if i != 5))


def test_yield_change_uses_the_5th_previous_valid_observation():
    f2 = pd.DataFrame({
        "trade_date_syd": ["2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02",
                           "2026-10-05", "2026-10-06", "2026-10-07"],
        "value_pct": [5.300, 5.310, 5.344, 5.350, 5.334, None, 5.394, 5.402]})
    out = add_yield_change_5obs(f2).set_index("trade_date_syd").yield_change_5obs_bp
    assert out.iloc[:5].isna().all()                               # fewer than 6 valid observations
    assert pd.isna(out["2026-10-05"])                              # blank RBA date: no change, no zero
    assert out["2026-10-06"] == pytest.approx((5.394 - 5.300) * 100)   # skips the blank date: 9.4 bp
    assert out["2026-10-07"] == pytest.approx((5.402 - 5.310) * 100)   # 9.2 bp
