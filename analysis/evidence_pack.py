"""Freeze the figures the report and the video quote, recomputed from the committed data.

    python analysis/evidence_pack.py     # writes docs/evidence/figures_<latest session>.md

Part 1 from the quality logs, Part 2 from analysis/part2_evidence.py, Part 3 with the same rules
the dashboard applies in the page (dashboard/common.js `stats`), so the report, the video and the
dashboard quote the same numbers. Re-run after a new data cut and quote the new file.
"""
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dashboard import build, indicators as ind  # noqa: E402
from pipeline.config import CURATED, QUALITY, SYD  # noqa: E402


def part1() -> list[tuple[str, str]]:
    log = pd.read_csv(QUALITY / "dq_run_log.csv")
    ev = pd.read_csv(QUALITY / "dq_events.csv")
    real, sim = log[~log.simulated.astype(bool)], log[log.simulated.astype(bool)]
    runs = real.drop_duplicates("run_id")
    by_status = real.groupby(["source", "status"]).size().to_dict()
    sched = runs[pd.to_datetime(runs.run_at_utc, utc=True) >= "2026-10-26"]
    started = pd.to_datetime(sched.run_at_utc, utc=True).dt.tz_convert(SYD).dt.strftime("%a %-d %b %H:%M")
    return [
        ("Real pipeline runs logged (both sources per run)", f"{len(runs)} runs, {len(real)} source rows"),
        ("Status by source (real runs)", ", ".join(f"{s} {st}: {n}" for (s, st), n in sorted(by_status.items()))),
        ("Simulated failure runs (demos)", f"{len(sim.drop_duplicates('run_id'))} runs; statuses seen: " + ", ".join(sorted(sim.status.unique()))),
        ("Real run start times, Sydney (the schedule is set for 18:17 Sydney on weekdays)", ", ".join(started)),
        ("Quality events by rule", ", ".join(f"{k} {v}" for k, v in ev.groupby("rule_id").size().items())),
        ("Rows quarantined (latest real ASX run)", str(int(real[real.source == "asx200"].rows_quarantined.iloc[-1]))),
        ("Latest RBA file publication date", str(real[real.source == "au10y"].detail.iloc[-1]).replace("RBA publication date ", "")),
    ]


def pearson(x, y):
    r = np.corrcoef(x, y)[0, 1]
    b = np.cov(x, y, ddof=0)[0, 1] / np.var(x)
    return r, b


def part3(m: dict, days: int = 90) -> list[tuple[str, str]]:
    rows = pd.DataFrame(m["rows"])
    end = date.fromisoformat(m["latest"]["end"])
    R = rows[rows.trade_date_syd >= (end - timedelta(days=days - 1)).isoformat()]
    closes = R.dropna(subset=["close_pts"])
    known = R.dropna(subset=["yield_same_day_pct"])
    pairs = R.dropna(subset=["asx_return_pct", "yield_change_1d_bp"])
    corr = R.corr20.dropna()
    r, b = pearson(pairs.yield_change_1d_bp, pairs.asx_return_pct)
    count = R.rag_status.value_counts()
    fired = R[R.rag_status.isin(["Amber", "Red"])]
    L = m["latest"]
    return [
        ("Window (dashboard default)", f"{R.trade_date_syd.min()} to {R.trade_date_syd.max()}, {len(R)} sessions"),
        ("Latest ASX session", f"{L['end']} ({L['end_status']}), close {L['close']:,.1f}"),
        ("Latest completed signal", f"{L['rag_status']} on {L['rag_date']} ({L['rag_pct']:+.0f}% vs its 20-session normal)"),
        ("ASX 200 change over the window", f"{(closes.close_pts.iloc[-1] / closes.close_pts.iloc[0] - 1) * 100:+.1f}% "
                                           f"({closes.close_pts.iloc[0]:,.1f} to {closes.close_pts.iloc[-1]:,.1f})"),
        ("10-year yield change over the window (same-day RBA data)",
         f"{(known.yield_same_day_pct.iloc[-1] - known.yield_same_day_pct.iloc[0]) * 100:+.0f} bp "
         f"({known.yield_same_day_pct.iloc[0]:.3f}% on {known.trade_date_syd.iloc[0]} to {known.yield_same_day_pct.iloc[-1]:.3f}% on {known.trade_date_syd.iloc[-1]})"),
        ("Yield shown on the dashboard (as at the 6 pm review)", f"{L['yield_asat']:.3f}% as at {L['yield_obs_date']} ({L['yield_age']} sessions old); "
                                                                f"latest 5-RBA-day change {L['yield_change_5obs_bp']:+.1f} bp"),
        ("Close vs 20-session average (latest)", f"{L['close_vs_ma20_pct']:+.1f}% (average {L['ma20']:,.1f})"),
        ("Volatility (latest) vs 1-year median", f"{L['vol20']:.1f}% vs {L['vol20_1y_median']:.1f}% (80th percentile {L['vol20_1y_p80']:.1f}%)"),
        ("Signal mix", ", ".join(f"{k} {int(count.get(k, 0))}" for k in ["Green", "Amber", "Red", "Pending", "Excluded"])),
        ("Sessions that triggered (Amber or Red)", "; ".join(f"{d} {s} {p:+.0f}%" for d, s, p in
                                                          fired[["trade_date_syd", "rag_status", "volume_vs_normal_pct"]].itertuples(index=False))),
        ("Rolling 20-session correlation", f"latest {corr.iloc[-1]:+.2f}, range {corr.min():+.2f} to {corr.max():+.2f}"),
        ("Scatter: daily ASX return vs same-day yield change", f"r = {r:+.2f}, n = {len(pairs)}, slope {b:+.3f} pp per +1 bp"),
        ("Thresholds (M4 v1.2)", f"Amber from +{m['thresholds']['amber']:.0f}%, Red from +{m['thresholds']['red']:.0f}% vs the previous 20 final volumes"),
    ]


def table(rows):
    return "| Figure | Value |\n| --- | --- |\n" + "\n".join(f"| {a} | {b} |" for a, b in rows) + "\n"


def main() -> int:
    m = build.model(build._read(build.SERVE), build._read(CURATED / "au10y_daily.csv"), build.last_fetch(),
                    build._read(CURATED / "asx200_daily.csv"))
    end = m["latest"]["end"]
    p2 = subprocess.run([sys.executable, str(ROOT / "analysis/part2_evidence.py"), end], capture_output=True, text=True, check=True).stdout
    p2rows = [(line[:66].strip(), line[66:].strip()) for line in p2.splitlines() if line.strip()]
    out = ROOT / "docs" / "evidence" / f"figures_{end}.md"
    stamp = datetime.now(timezone.utc).astimezone(SYD).strftime("%a %-d %b %Y, %H:%M Sydney")
    out.write_text(
        f"# Evidence pack: figures as at the {end} data cut\n\n"
        f"Generated by `analysis/evidence_pack.py` on {stamp} from the committed data (last fetch {m['fetched']}). "
        "Quote these in the report and the video so every number matches the dashboard. Numbers are rounded for display; "
        "the calculations use full precision.\n\n"
        "## Part 1: pipeline and data quality\n\n" + table(part1()) +
        "\n## Part 2: metrics on the Sydney time axis (`analysis/part2_evidence.py`)\n\n" + table(p2rows) +
        "\n## Part 3: dashboard, default 90-day view\n\n" + table(part3(m)) +
        "\n## Notes\n\n"
        "- The latest session is provisional at the data cut, so its volume is not final and the signal for it is Pending; "
        "the latest completed signal is the session before.\n"
        "- The RBA publishes F2 weekly, so the same-day yield stops at the newest published observation; the dashboard shows "
        "that gap as \"Awaiting RBA release\".\n"
        "- Correlation and the scatter describe association, not causation.\n")
    print(f"Wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
