"""Run the Part 1 pipeline for both sources.

    python -m pipeline.run                       # normal scheduled run
    python -m pipeline.run --simulate 429        # demo: rate limit -> retries -> keep last good load
    python -m pipeline.run --simulate late       # demo: F2 release missing -> 'late' status
    python -m pipeline.run --simulate schema     # demo: F2 series ID changed -> load stopped
    python -m pipeline.run --as-of 2026-10-22T18:00+11:00   # evaluate the release clock at a past moment

Simulated runs write to the quality log (marked simulated) but never change clean tables.
Simulated 'late' and 'schema' runs replay the last good raw snapshot, so they never call a provider.
Exit code 1 means a load was stopped, or a source was late or stale on two consecutive real runs; the
scheduled workflow then opens a GitHub issue for the data owner.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import pandas as pd
import requests

from . import store
from .config import QUALITY, QUARANTINE, SYD, sources
from .http import FetchError, fetch
from .ingest_rba_f2 import SchemaError, parse_f2
from .ingest_yahoo import parse_chart
from .release_calendar import expected_through
from .validate import RULES, validate_asx, validate_f2


class _RateLimited:
    """A fake HTTP session that always answers 429, for the failure demo."""
    def get(self, url, **_):
        r = requests.Response()
        r.status_code, r._content, r.url = 429, b"Too Many Requests", url
        r.headers["Retry-After"] = "1"
        return r


def _say(msg: str) -> None:
    print(msg, flush=True)


def _base_row(run_id, now, as_of, simulate, source):
    return {"run_id": run_id, "run_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "as_of_syd": as_of.astimezone(SYD).isoformat(timespec="minutes"),
            "simulated": simulate != "none", "source": source, "status": "", "rows_in": 0,
            "rows_clean": 0, "rows_quarantined": 0, "rows_flagged": 0, "expected_through": "",
            "received_through": "", "fetch_attempts": "", "raw_path": "", "quarantine_path": "", "detail": ""}


def run_asx(cfg, run_id, now, as_of, simulate, session) -> dict:
    row = _base_row(run_id, now, as_of, simulate, "asx200")
    first = not (store.CURATED / "asx200_daily.csv").exists()
    params = {"range": "2y" if first else "1mo", "interval": "1d"}
    replay = store.read_latest_raw("asx200", "json") if simulate in ("late", "schema") else None
    if replay:
        df, _ = parse_chart(replay[0])
        result = validate_asx(df, run_id, cfg["exchange_timezone"])
        row.update(result.counts(), status="ok", detail=f"simulation replayed {replay[1]}",
                   received_through=result.clean.trade_date_syd.max() if len(result.clean) else "")
        return row
    try:
        res = fetch(cfg["url"], params, session=_RateLimited() if simulate == "429" else session,
                    backoff=(1, 2, 4) if simulate == "429" else (2, 8, 30))
    except FetchError as exc:
        row.update(status="stale", fetch_attempts=json.dumps(exc.attempts),
                   detail=f"{exc}; kept last good load ({store.latest_raw('asx200', 'json')})")
        store.log_events([{"run_id": run_id, "source": "asx200", "record_key": "fetch", "rule_id": "DQ06",
                           "dimension": "timeliness", "action": "alert", "detail": row["detail"]}])
        for a in exc.attempts:
            _say(f"  asx200 attempt {a['attempt']}: HTTP {a['http_status']} ({a['latency_ms']} ms)")
        return row
    row["fetch_attempts"] = json.dumps(res.attempts)
    raw_path = "" if simulate != "none" else store.write_raw(
        "asx200", run_id, res.content, "json", now, {"source": "asx200", "url": res.url, "params": params})
    row["raw_path"] = str(raw_path)
    df, _ = parse_chart(res.content)
    result = validate_asx(df, run_id, cfg["exchange_timezone"])
    row.update(result.counts(), status="ok",
               received_through=result.clean.trade_date_syd.max() if len(result.clean) else "")
    row["quarantine_path"] = store.write_quarantine(run_id, "asx200", result.quarantine)
    store.log_events(result.events)
    if simulate == "none":
        store.upsert_asx(result.clean, run_id)
    return row


def run_f2(cfg, run_id, now, as_of, simulate, session) -> dict:
    row = _base_row(run_id, now, as_of, simulate, "au10y")
    exp = expected_through(as_of)
    row["expected_through"] = exp.isoformat()
    replay = store.read_latest_raw("au10y", "csv") if simulate in ("late", "schema") else None
    if replay:
        content, url = replay[0], replay[1]
        row["detail"] = f"simulation replayed {replay[1]}"
    else:
        try:
            res = fetch(cfg["url"], session=_RateLimited() if simulate == "429" else session,
                        backoff=(1, 2, 4) if simulate == "429" else (2, 8, 30))
        except FetchError as exc:
            row.update(status="stale", fetch_attempts=json.dumps(exc.attempts),
                       detail=f"{exc}; kept last good load ({store.latest_raw('au10y', 'csv')})")
            for a in exc.attempts:
                _say(f"  au10y attempt {a['attempt']}: HTTP {a['http_status']} ({a['latency_ms']} ms)")
            return row
        row["fetch_attempts"] = json.dumps(res.attempts)
        content, url = res.content, res.url
    if simulate == "schema":   # the RBA renames the series: the contract no longer holds
        content = content.replace(cfg["series_id"].encode(), (cfg["series_id"] + "X").encode())
    raw_path = "" if simulate != "none" else store.write_raw(
        "au10y", run_id, content, "csv", now, {"source": "au10y", "url": url})
    row["raw_path"] = str(raw_path)
    try:
        df, info = parse_f2(content, cfg["series_id"], cfg["expected_units"])
    except SchemaError as exc:
        q = QUARANTINE / f"{run_id}_au10y_snapshot.csv"
        q.parent.mkdir(parents=True, exist_ok=True)
        q.write_bytes(content)
        rule = RULES["DQ07"]
        store.log_events([{"run_id": run_id, "source": "au10y", "record_key": "file", "rule_id": "DQ07",
                           "dimension": rule["dimension"], "action": rule["action"], "detail": str(exc)}])
        row.update(status="stopped", detail=f"DQ07 schema guard: {exc}" + (f" ({row['detail']})" if row["detail"] else ""),
                   quarantine_path=str(q.relative_to(QUALITY.parent.parent)))
        return row
    result = validate_f2(df, run_id)
    clean = result.clean
    if simulate == "late":     # pretend the latest weekly release never arrived
        cutoff = (pd.Timestamp(exp) - pd.offsets.BDay(5)).strftime("%Y-%m-%d")
        clean = clean[clean.trade_date_syd <= cutoff]
        result.clean = clean
    received = clean.loc[clean.value_pct.notna(), "trade_date_syd"].max()
    row.update(result.counts(), received_through=received, status="ok",
               detail="; ".join(x for x in (row["detail"], f"RBA publication date {info.get('publication_date')}") if x))
    if simulate == "late":
        row["detail"] += f"; simulated: the release covering dates after {cutoff} never arrived"
    events = list(result.events)
    if received < exp.isoformat():
        row["status"] = "late"
        events.append({"run_id": run_id, "source": "au10y", "record_key": "release", "rule_id": "DQ06",
                       "dimension": "timeliness", "action": "alert",
                       "detail": f"expected data through {exp}, received through {received}"})
    if simulate == "none":
        _, revisions = store.upsert_f2(clean, run_id, now)
        for r in revisions.itertuples():
            events.append({"run_id": run_id, "source": "au10y", "record_key": r.trade_date_syd, "rule_id": "DQ08",
                           "dimension": "consistency", "action": "flag",
                           "detail": f"revised {r.old_value_pct} -> {r.new_value_pct}"})
        if len(revisions):
            row["detail"] += f"; {len(revisions)} revision(s) logged"
    row["quarantine_path"] = store.write_quarantine(run_id, "au10y", result.quarantine)
    store.log_events(events)
    return row


def summary_markdown(rows: list[dict], run_id: str) -> str:
    lines = [f"# Pipeline run {run_id}", "",
             "| Source | Status | In | Clean | Quarantined | Flagged | Expected through | Received through | Detail |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        lines.append(f"| {r['source']} | **{r['status']}** | {r['rows_in']} | {r['rows_clean']} | "
                     f"{r['rows_quarantined']} | {r['rows_flagged']} | {r['expected_through']} | "
                     f"{r['received_through']} | {r['detail']} |")
    lines += ["", "Status meanings: ok = loaded; late = RBA release behind schedule (dashboard shows 'as at');",
              "stale = source unreachable, last good load kept; stopped = data contract broken, nothing loaded."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--simulate", choices=["none", "429", "late", "schema"], default="none")
    p.add_argument("--as-of", help="ISO datetime with offset, e.g. 2026-10-22T18:00+11:00 (default: now)")
    args = p.parse_args(argv)

    now = datetime.now(timezone.utc)
    as_of = datetime.fromisoformat(args.as_of) if args.as_of else now
    run_id = now.strftime("%Y%m%dT%H%M%SZ") + ("" if args.simulate == "none" else f"-sim{args.simulate}")
    cfg = sources()
    session = requests.Session()
    _say(f"Run {run_id} | as of {as_of.astimezone(SYD):%a %d %b %Y %H:%M} Sydney | simulate={args.simulate}")

    rows = []
    for name, fn in (("asx200", run_asx), ("au10y", run_f2)):
        prev = store.previous_status(name)
        try:
            row = fn(cfg[name], run_id, now, as_of, args.simulate, session)
        except Exception as exc:           # reconciliation broke or an unexpected error: fail loudly, keep going
            row = _base_row(run_id, now, as_of, args.simulate, name)
            row.update(status="failed", detail=f"{type(exc).__name__}: {exc}")
        row["previous_status"] = prev or ""
        store.log_run(row)
        rows.append(row)
        _say(f"  {name}: {row['status']} | in {row['rows_in']} = clean {row['rows_clean']} + "
             f"quarantined {row['rows_quarantined']} | flagged {row['rows_flagged']} | "
             f"through {row['received_through'] or '-'} (expected {row['expected_through'] or 'n/a'})")
        if row["detail"]:
            _say(f"    {row['detail']}")
        time.sleep(1)

    md = summary_markdown(rows, run_id)
    (QUALITY / "last_run_summary.md").write_text(md)
    for r in rows:   # a yellow warning on the GitHub run page: visible, but not an alarm
        if r["status"] in ("late", "stale") and os.environ.get("GITHUB_ACTIONS") == "true":
            print(f"::warning title={r['source']} {r['status']}::{r['detail']}", flush=True)
    if needs_alert(rows, args.simulate):
        _say("ALERT: data owner action needed (see data/quality/last_run_summary.md)")
        return 1
    return 0


def needs_alert(rows: list[dict], simulate: str) -> bool:
    """Escalation policy.

    A broken contract or failed run alerts at once. A single late or stale run does not:
    the dashboard already shows 'as at', and alerting on every slow RBA release would train
    people to ignore alerts. The same problem on two consecutive *real* runs escalates.
    """
    if any(r["status"] in ("stopped", "failed") for r in rows):
        return True
    return simulate == "none" and any(
        r["status"] in ("late", "stale") and r["previous_status"] == r["status"] for r in rows)


if __name__ == "__main__":
    sys.exit(main())
