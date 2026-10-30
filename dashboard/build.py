"""Build the Part 3 dashboard from the serve table.

    python -m dashboard.build                       # writes docs/dashboard/index.html
    python -m dashboard.build --fragment out.html   # also writes the page body only (for previews)

Reads data/serve/daily_panel.csv (Part 2), data/curated/au10y_daily.csv (daily yield changes)
and data/quality/dq_run_log.csv (when the data was last fetched). Writes one self-contained
HTML page (Plotly.js from a CDN). The page holds one year of sessions so the reader can switch
between 1W, 1M, 3M (the brief's 90 days, the default) and 1Y; the range summaries are computed
in the page from these rows.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from pipeline.config import CURATED, QUALITY, SYD

from . import indicators as ind

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "dashboard" / "index.html"
SERVE = CURATED.parent / "serve" / "daily_panel.csv"
HISTORY_DAYS = 365          # the longest range button (1Y)
ROW_COLS = ["trade_date_syd", "bar_status", "open_pts", "high_pts", "low_pts", "close_pts", "ma20_pts", "vol20_ann_pct", "volume", "volume_normal",
            "volume_vs_normal_pct", "rag_status", "yield_same_day_pct", "yield_asat_pct", "yield_asat_obs_date",
            "yield_asat_age_sessions", "yield_change_5obs_bp", "asx_return_pct", "yield_change_1d_bp", "corr20"]
SOURCES = [
    "S&amp;P/ASX 200 index (^AXJO), daily bars: Yahoo Finance.",
    "Australian Government 10-year bond yield (FCMYGBAG10D): Reserve Bank of Australia, Statistical Table F2 "
    "\"Capital Market Yields – Government Bonds\".",
]


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"dq_flags": str}, keep_default_na=False, na_values=[""])


def _clean(v):
    if v is None or v is pd.NA or (isinstance(v, float) and math.isnan(v)):
        return None
    if hasattr(v, "item"):
        v = v.item()
    return round(v, 6) if isinstance(v, float) else v


def last_fetch(log_path: Path = QUALITY / "dq_run_log.csv") -> str | None:
    """Sydney time of the newest real (not simulated) pipeline run."""
    if not log_path.exists():
        return None
    log = pd.read_csv(log_path)
    log = log[~log.simulated.astype(bool)]
    if log.empty:
        return None
    t = pd.to_datetime(log.run_at_utc.max(), utc=True).tz_convert(SYD)
    return t.strftime("%a %-d %b %Y, %H:%M Sydney")


def model(panel: pd.DataFrame, f2: pd.DataFrame, fetched: str | None = None,
          ohlc: pd.DataFrame | None = None) -> dict:
    """Everything the page needs, as plain data (tested in tests/test_dashboard.py)."""
    if ohlc is not None:     # open/high/low for the optional candle view (curated ASX table)
        o = ohlc[["trade_date_syd", "open", "high", "low"]].rename(columns=lambda c: c if c == "trade_date_syd" else c + "_pts")
        panel = panel.merge(o, on="trade_date_syd", how="left")
    else:
        panel = panel.assign(open_pts=None, high_pts=None, low_pts=None)
    full = ind.add_corr20(ind.add_rag(ind.add_volume_vs_normal(panel)), f2)
    end = date.fromisoformat(full.trade_date_syd.max())
    hist = full[full.trade_date_syd > (end - timedelta(days=HISTORY_DAYS)).isoformat()]
    s = ind.summary(ind.window(full), full)
    latest = {k: _clean(s[k]) for k in ("end", "end_status", "close", "ma20", "close_vs_ma20_pct", "vol20",
                                        "vol20_1y_median", "vol20_1y_p80", "yield_asat", "yield_obs_date",
                                        "yield_age", "yield_change_5obs_bp", "rag_date", "rag_status", "rag_pct")}
    rows = [{c: _clean(r[c]) for c in ROW_COLS} for _, r in hist.iterrows()]
    return {"latest": latest, "rows": rows, "default_days": ind.WINDOW_DAYS, "sources": SOURCES,
            "thresholds": {"amber": ind.AMBER_AT * 100, "red": ind.RED_AT * 100},
            "fetched": fetched or "unknown",
            "built": datetime.now(timezone.utc).astimezone(SYD).strftime("%a %-d %b %Y, %H:%M Sydney"),
            "summary_90d": {k: _clean(v) for k, v in s.items() if not isinstance(v, list)}}


def render(m: dict) -> str:
    """The page body (title, styles, markup, script) with the data embedded."""
    data = json.dumps(m, ensure_ascii=False, allow_nan=False).replace("</", "<\\/")
    return (HERE / "template.html").read_text().replace("/*__DATA__*/", data)


def page(fragment: str) -> str:
    """A complete HTML document for GitHub Pages or opening locally."""
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f"</head>\n<body>\n{fragment}\n</body>\n</html>\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fragment", help="also write the page body only to this path")
    args = ap.parse_args(argv)
    m = model(_read(SERVE), _read(CURATED / "au10y_daily.csv"), last_fetch(), _read(CURATED / "asx200_daily.csv"))
    body = render(m)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page(body))
    if args.fragment:
        Path(args.fragment).write_text(body)
    s = m["summary_90d"]
    print(f"Dashboard built: {OUT.relative_to(HERE.parent)} | {len(m['rows'])} sessions (1 year) | default "
          f"{s['start']} to {s['end']} | signal {s['rag_status']} ({s['rag_date']}) | "
          f"fired {s['fired_amber']} Amber, {s['fired_red']} Red | last fetch {m['fetched']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
