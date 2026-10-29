"""Storage: write-once raw snapshots, clean tables, F2 vintages and the quality log.

Raw files are never modified. Clean tables are rebuilt by upsert from what each run read.
Every F2 value keeps a vintage row (when we first saw it, or when the RBA would have
published it for history we did not witness), so later joins can be point-in-time.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from .config import CURATED, QUALITY, QUARANTINE, RAW, SYD
from .release_calendar import RELEASE_TIME, release_covering


def write_raw(source: str, run_id: str, content: bytes, ext: str, fetched_at: datetime, manifest: dict) -> Path:
    folder = RAW / source / fetched_at.astimezone(SYD).date().isoformat()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{run_id}.{ext}"
    if path.exists():
        raise FileExistsError(f"raw snapshot {path} already exists; raw data is write-once")
    path.write_bytes(content)
    manifest = {**manifest, "run_id": run_id, "fetched_at_utc": fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
                "path": str(path.relative_to(RAW.parent.parent))}
    (folder / f"{run_id}.manifest.json").write_text(json.dumps(manifest, indent=2))
    return path.relative_to(RAW.parent.parent)


def latest_raw(source: str, ext: str) -> Path | None:
    files = sorted(p for p in (RAW / source).glob(f"*/*.{ext}") if not p.name.endswith(".manifest.json"))
    return files[-1].relative_to(RAW.parent.parent) if files else None


def read_latest_raw(source: str, ext: str) -> tuple[bytes, str] | None:
    """Bytes and repo-relative path of the newest raw snapshot (the 'last good load')."""
    rel = latest_raw(source, ext)
    return None if rel is None else ((RAW.parent.parent / rel).read_bytes(), str(rel))


def append_csv(path: Path, df: pd.DataFrame) -> None:
    if df.empty:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, mode="a", header=not path.exists(), index=False)


def upsert_asx(clean: pd.DataFrame, run_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Update the ASX clean table. Returns (merged table, closes that changed).

    The latest session usually arrives as a provisional bar and is replaced by the final bar
    on the next run. A replacement that changes the close is returned so it can be logged
    (DQ08), never overwritten silently.
    """
    path = CURATED / "asx200_daily.csv"
    new = clean.assign(last_seen_run_id=run_id)
    revisions = pd.DataFrame(columns=["trade_date_syd", "old_close", "new_close"])
    if path.exists():
        old = pd.read_csv(path, dtype={"dq_flags": str}, keep_default_na=False, na_values=[""])
        both = old[["trade_date_syd", "close"]].merge(new[["trade_date_syd", "close"]], on="trade_date_syd",
                                                       suffixes=("_old", "_new"))
        changed = both[(both.close_old - both.close_new).abs() > 1e-9]
        revisions = changed.rename(columns={"close_old": "old_close", "close_new": "new_close"})
        merged = pd.concat([old[~old.trade_date_syd.isin(new.trade_date_syd)], new])
    else:
        merged = new
    merged = merged.sort_values("trade_date_syd").reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(path, index=False)
    return merged, revisions.reset_index(drop=True)


def published_at(publication_date: str | None) -> datetime | None:
    """The RBA's 'Publication date' header (e.g. '23-Oct-2026') at the 2:00 pm release time."""
    try:
        return datetime.combine(datetime.strptime(publication_date, "%d-%b-%Y").date(), RELEASE_TIME, SYD)
    except (TypeError, ValueError):
        return None


def upsert_f2(clean: pd.DataFrame, run_id: str, seen_at: datetime,
              publication_date: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Update the F2 clean table and vintages. Returns (merged table, revisions).

    A new or revised value is available from the file's own publication time, but never
    later than when we first saw it. Using the publication time (not our download time)
    keeps availability right when the scheduled run starts hours late, as GitHub runs can.
    """
    path = CURATED / "au10y_daily.csv"
    vint_path = CURATED / "au10y_vintages.csv"
    first_run = not path.exists()
    old = (pd.read_csv(path, dtype={"dq_flags": str}, keep_default_na=False, na_values=[""])
           if not first_run else pd.DataFrame(columns=["trade_date_syd", "value_pct", "dq_flags"]))
    old_vals = dict(zip(old.trade_date_syd, old.value_pct))
    seen_syd = seen_at.astimezone(SYD).isoformat(timespec="minutes")
    pub = published_at(publication_date)
    live_avail = (min(seen_at, pub) if pub else seen_at).astimezone(SYD).isoformat(timespec="minutes")

    vintages, revisions = [], []
    for r in clean.itertuples():
        if pd.isna(r.value_pct):
            continue
        before = old_vals.get(r.trade_date_syd)
        if first_run:
            change, avail, recon = "initial_backfill", release_covering(
                datetime.strptime(r.trade_date_syd, "%Y-%m-%d").date()).isoformat(timespec="minutes"), True
        elif before is None or pd.isna(before):
            change, avail, recon = "new", live_avail, False
        elif abs(before - r.value_pct) > 1e-9:
            change, avail, recon = "revised", live_avail, False
            revisions.append({"trade_date_syd": r.trade_date_syd, "old_value_pct": before, "new_value_pct": r.value_pct})
        else:
            continue
        vintages.append({"trade_date_syd": r.trade_date_syd, "value_pct": r.value_pct, "change": change,
                         "seen_run_id": run_id, "seen_at_syd": seen_syd,
                         "available_from_syd": avail, "availability_reconstructed": recon})
    append_csv(vint_path, pd.DataFrame(vintages))

    # current availability = latest vintage per date
    vint = pd.read_csv(vint_path) if vint_path.exists() else pd.DataFrame(
        columns=["trade_date_syd", "available_from_syd", "availability_reconstructed"])
    latest = vint.drop_duplicates("trade_date_syd", keep="last")[
        ["trade_date_syd", "available_from_syd", "availability_reconstructed"]]
    merged = pd.concat([old[~old.trade_date_syd.isin(clean.trade_date_syd)][["trade_date_syd", "value_pct", "dq_flags"]],
                        clean[["trade_date_syd", "value_pct", "dq_flags"]]])
    merged = merged.merge(latest, on="trade_date_syd", how="left").assign(last_seen_run_id=run_id)
    merged = merged.sort_values("trade_date_syd").reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(path, index=False)
    return merged, pd.DataFrame(revisions)


def log_run(row: dict) -> None:
    append_csv(QUALITY / "dq_run_log.csv", pd.DataFrame([row]))


def log_events(events: list[dict]) -> None:
    append_csv(QUALITY / "dq_events.csv", pd.DataFrame(events))


def write_quarantine(run_id: str, source: str, df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    path = QUARANTINE / f"{run_id}_{source}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return str(path.relative_to(QUALITY.parent.parent))


def previous_status(source: str) -> str | None:
    path = QUALITY / "dq_run_log.csv"
    if not path.exists():
        return None
    log = pd.read_csv(path)
    log = log[(log.source == source) & (~log.simulated.astype(bool))]
    return None if log.empty else str(log.iloc[-1].status)
