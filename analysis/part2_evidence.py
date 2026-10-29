"""Part 2 evidence: the numbers quoted in the report, recomputed from the committed data.

    python analysis/part2_evidence.py            # window ends at the latest session
    python analysis/part2_evidence.py 2026-10-28 # window ends at a fixed session

Reads data/serve/daily_panel.csv (rebuild it first with `python -m pipeline.align`).
"""
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.metrics import add_yield_change_5obs  # noqa: E402

panel = pd.read_csv(ROOT / "data/serve/daily_panel.csv")
end = sys.argv[1] if len(sys.argv) > 1 else panel.trade_date_syd.max()
panel = panel[panel.trade_date_syd <= end]
start90 = (date.fromisoformat(end) - timedelta(days=90)).isoformat()
start1y = (date.fromisoformat(end) - timedelta(days=365)).isoformat()
w = panel[panel.trade_date_syd > start90]
y1 = panel[panel.trade_date_syd > start1y]

f2 = add_yield_change_5obs(pd.read_csv(ROOT / "data/curated/au10y_daily.csv")).set_index("trade_date_syd")
panel = panel.assign(same_day_change_bp=panel.trade_date_syd.map(f2.yield_change_5obs_bp))


def rng(s, fmt="{:,.2f}"):
    return f"{fmt.format(s.min())} to {fmt.format(s.max())}"


def opposite(df):
    b = df.dropna(subset=["same_day_change_bp", "yield_change_5obs_bp"])
    b = b[(b.same_day_change_bp != 0) & (b.yield_change_5obs_bp != 0)]
    n = int((np.sign(b.same_day_change_bp) != np.sign(b.yield_change_5obs_bp)).sum())
    return f"{n} of {len(b)} ({n / len(b):.0%})" if len(b) else "n/a"


p80 = y1.vol20_ann_pct.quantile(0.8)
known = panel.dropna(subset=["yield_same_day_pct"])
gap = (known.yield_asat_pct - known.yield_same_day_pct).abs() * 100
rows = [
    ("Window (90 calendar days)", f"{w.trade_date_syd.min()} to {end}, {len(w)} sessions"),
    ("ASX close, pts", rng(w.close_pts)),
    ("20-session average, pts", rng(w.ma20_pts)),
    ("Sessions closing above their average", f"{int((w.close_pts > w.ma20_pts).sum())} of {len(w)}"),
    ("20-session volatility, % a year", rng(w.vol20_ann_pct)),
    ("Volatility 1-year median / 80th percentile", f"{y1.vol20_ann_pct.median():.1f} / {p80:.1f}"),
    ("Sessions above the 1-year 80th percentile (90 days)", str(int((w.vol20_ann_pct > p80).sum()))),
    ("10-year yield as at 6 pm, %", rng(w.yield_asat_pct, "{:.2f}")),
    ("5-observation change as at 6 pm, bp", rng(w.yield_change_5obs_bp, "{:+.1f}")),
    ("Size of that change: median / 90th percentile, bp",
     f"{w.yield_change_5obs_bp.abs().median():.1f} / {w.yield_change_5obs_bp.abs().quantile(0.9):.1f}"),
    ("Yield age at the review, sessions (all history)",
     f"{rng(panel.yield_asat_age_sessions, '{:.0f}')}, average {panel.yield_asat_age_sessions.mean():.1f}"),
    ("As-at vs same-dated yield, bp (all history)", f"average {gap.mean():.1f}, max {gap.max():.1f}, {len(gap)} sessions"),
    ("As-at change opposite in sign to same-dated change (all history)", opposite(panel)),
    ("... in the 90-day window", opposite(panel[panel.trade_date_syd > start90])),
]
width = max(len(k) for k, _ in rows)
for k, v in rows:
    print(f"{k:<{width}}  {v}")
