"""Build the Part 3 dashboard from the serve table.

    python -m dashboard.build                       # writes docs/dashboard/index.html
    python -m dashboard.build --fragment out.html   # also writes the page body only (for previews)

Reads data/serve/daily_panel.csv (Part 2) and data/curated/au10y_daily.csv (for the daily
yield change in the correlation). Writes one self-contained HTML page (Plotly.js from a CDN),
so it can be opened locally, published on GitHub Pages, or attached to the report.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from pipeline.config import CURATED, SYD

from . import indicators as ind

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "dashboard" / "index.html"
SERVE = CURATED.parent / "serve" / "daily_panel.csv"
ROW_COLS = ["trade_date_syd", "bar_status", "close_pts", "ma20_pts", "vol20_ann_pct", "volume", "volume_normal",
            "volume_vs_normal_pct", "rag_status", "yield_same_day_pct", "yield_asat_pct", "yield_asat_obs_date",
            "yield_asat_age_sessions", "yield_change_5obs_bp", "corr20"]


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"dq_flags": str}, keep_default_na=False, na_values=[""])


def _clean(v):
    if v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NA:
        return None
    if hasattr(v, "item"):
        v = v.item()
    return round(v, 6) if isinstance(v, float) else v


def _signed(v: float, d: int) -> str:
    """+1.3 / −0.35 with a true minus sign."""
    return f"{v:+.{d}f}".replace("-", "\u2212")


def model(panel: pd.DataFrame, f2: pd.DataFrame) -> dict:
    """Everything the page shows, as plain data (tested in tests/test_dashboard.py)."""
    full = ind.add_corr20(ind.add_rag(ind.add_volume_vs_normal(panel)), f2)
    w = ind.window(full)
    s = ind.summary(w, full)
    rows = [{c: _clean(r[c]) for c in ROW_COLS} for _, r in w.iterrows()]
    known = w.dropna(subset=["yield_same_day_pct"])
    y_bp = (known.yield_same_day_pct.iloc[-1] - known.yield_same_day_pct.iloc[0]) * 100 if len(known) > 1 else 0.0
    fired = s["fired_amber"] + s["fired_red"]
    up_down = "down" if s["close_change_pct"] < 0 else "up"
    rose_fell = "rose" if y_bp >= 0 else "fell"
    text = {
        "headline": f"ASX 200 {up_down} {abs(s['close_change_pct']):.1f}% in 90 days while the 10-year yield "
                    f"{rose_fell} {abs(y_bp):.0f} bp",
        "dek": (f"Shares and long-term rates kept moving in opposite directions. Trading volume ran well above "
                f"normal on {fired} of {s['sessions']} sessions; the latest final session is {s['rag_status']}."),
        "t_price": (f"The index closed {'above' if s['close_vs_ma20_pct'] >= 0 else 'below'} its 20-session average "
                    f"({_signed(s['close_vs_ma20_pct'], 1)}%)"),
        "t_vol": f"Volume spiked on {fired} sessions; {s['fired_red']} reached Red",
        "t_yield": (f"The 10-year yield {rose_fell} {abs(y_bp):.0f} bp to {known.yield_same_day_pct.iloc[-1]:.2f}% "
                    f"(RBA data to {pd.Timestamp(known.trade_date_syd.iloc[-1]):%-d %b})") if len(known) else "10-year yield",
        "t_corr": (f"Shares usually fell when yields rose: latest correlation {_signed(s['corr20'], 2)} "
                   f"(range {_signed(s['corr20_min'], 2)} to {_signed(s['corr20_max'], 2)})") if s["corr20"] is not None else "Correlation",
        "notes": [
            "Sources: S&amp;P/ASX 200 (^AXJO) daily bars from Yahoo Finance; Australian Government 10-year bond yield "
            "(FCMYGBAG10D) from RBA Statistical Table F2, which the RBA describes as its assessment of closing yields, "
            "not financial benchmarks.",
            "Time axis: one row per ASX session in Sydney time. The \"as at 6 pm\" yield is the newest one the RBA had "
            "published by 6:00 pm Sydney that day; F2 is released weekly (Fridays, 2 pm), so it is usually 2 to 6 sessions old. "
            "The yield chart plots each yield on its own RBA date, which is only known after publication.",
            "Volume: Yahoo's index volume is much smaller than total market turnover; use it only to compare days. "
            "A session whose volume is not final shows as pending, never as zero.",
            "The volume signal (M4) is a draft for the team's review and is not yet in the metric definitions. "
            "Correlation uses the daily ASX log return and the same-day change in the RBA yield over 20 sessions.",
            "Definitions: docs/METRICS.md and docs/DATA_DICTIONARY.md in the project repository.",
        ],
    }
    built = datetime.now(timezone.utc).astimezone(SYD).strftime("%a %-d %b %Y, %H:%M Sydney")
    return {"summary": {k: _clean(v) if not isinstance(v, list) else [{kk: _clean(vv) for kk, vv in d.items()} for d in v]
                        for k, v in s.items()},
            "rows": rows, "text": text, "built": built}


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
    m = model(_read(SERVE), _read(CURATED / "au10y_daily.csv"))
    body = render(m)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page(body))
    if args.fragment:
        Path(args.fragment).write_text(body)
    s = m["summary"]
    print(f"Dashboard built: {OUT.relative_to(HERE.parent)} | {s['start']} to {s['end']} | "
          f"signal {s['rag_status']} ({s['rag_date']}) | fired {s['fired_amber']} Amber, {s['fired_red']} Red")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
