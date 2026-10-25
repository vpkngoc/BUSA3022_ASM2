"""Row-level data quality checks. Nothing is dropped silently.

Every row either passes into the clean table (possibly with flags) or goes to quarantine
with a rule ID and a reason. `rows_in == rows_clean + rows_quarantined` always holds, and
the run fails if it does not.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .config import dq_rules

RULES = dq_rules()


@dataclass
class Result:
    source: str
    clean: pd.DataFrame
    quarantine: pd.DataFrame
    events: list[dict] = field(default_factory=list)

    @property
    def rows_in(self) -> int:
        return len(self.clean) + len(self.quarantine)

    def counts(self) -> dict:
        flagged = int((self.clean["dq_flags"] != "").sum()) if len(self.clean) else 0
        return {"rows_in": self.rows_in, "rows_clean": len(self.clean),
                "rows_quarantined": len(self.quarantine), "rows_flagged": flagged}


def _event(run_id, source, key, rule_id, detail):
    rule = RULES[rule_id]
    return {"run_id": run_id, "source": source, "record_key": str(key), "rule_id": rule_id,
            "dimension": rule["dimension"], "action": rule["action"], "detail": detail}


def _add_flag(df: pd.DataFrame, mask: pd.Series, rule_id: str) -> None:
    df.loc[mask, "dq_flags"] = df.loc[mask, "dq_flags"].map(lambda f: f"{f};{rule_id}" if f else rule_id)


def validate_asx(raw: pd.DataFrame, run_id: str, tz: str = "Australia/Sydney") -> Result:
    src = "asx200"
    df = raw.copy().reset_index(drop=True)
    n_in = len(df)
    events: list[dict] = []
    ts = pd.to_datetime(df["epoch_s"], unit="s", utc=True, errors="coerce")
    local = ts.dt.tz_convert(tz)
    df["observed_at_utc"] = ts.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df["trade_date_syd"] = local.dt.strftime("%Y-%m-%d")   # Sydney date, never the UTC date
    df["local_time_syd"] = local.dt.strftime("%H:%M")
    df["reason"] = ""

    # DQ01 interpretability: timestamp parses, Sydney date is a weekday, a close exists
    bad_ts = ts.isna()
    weekend = ~bad_ts & (local.dt.weekday >= 5)
    no_close = ~bad_ts & ~weekend & df["close"].isna()
    df.loc[bad_ts, "reason"] = "DQ01: timestamp does not parse"
    df.loc[weekend, "reason"] = "DQ01: Sydney date falls on a weekend"
    df.loc[no_close, "reason"] = "DQ01: no closing value"
    rejected = bad_ts | weekend | no_close

    # DQ02 uniqueness: one bar per Sydney date; keep the bar stamped at the 10:00 open
    ok = df[~rejected].copy()
    ok["_open_stamp"] = ok["local_time_syd"] != "10:00"   # False sorts first
    ok = ok.sort_values(["trade_date_syd", "_open_stamp", "epoch_s"])
    dup_idx = ok.index[ok.duplicated("trade_date_syd", keep="first")]
    df.loc[dup_idx, "reason"] = df.loc[dup_idx].apply(
        lambda r: f"DQ02: second bar for {r.trade_date_syd} stamped {r.local_time_syd} (live/partial bar)", axis=1)
    rejected = rejected | df.index.isin(dup_idx)

    quarantine = df[rejected].copy()
    for _, r in quarantine.iterrows():
        events.append(_event(run_id, src, r["trade_date_syd"] or r["epoch_s"], r["reason"][:4], r["reason"]))

    clean = df[~rejected].sort_values("trade_date_syd").copy()
    clean["dq_flags"] = ""
    # DQ03 completeness: volume present and positive -> flag, keep row
    novol = clean["volume"].isna() | (clean["volume"] <= 0)
    _add_flag(clean, novol, "DQ03")
    for _, r in clean[novol].iterrows():
        events.append(_event(run_id, src, r.trade_date_syd, "DQ03", f"volume={r.volume}"))
    # DQ05 accuracy: daily move within 10%
    move = clean["close"].pct_change()
    big = move.abs() > 0.10
    _add_flag(clean, big, "DQ05")
    for i, r in clean[big].iterrows():
        events.append(_event(run_id, src, r.trade_date_syd, "DQ05", f"daily move {move[i]:+.1%}"))

    cols = ["trade_date_syd", "observed_at_utc", "open", "high", "low", "close", "volume", "dq_flags"]
    res = Result(src, clean[cols].reset_index(drop=True),
                 quarantine[["epoch_s", "observed_at_utc", "trade_date_syd", "local_time_syd",
                             "close", "volume", "reason"]].reset_index(drop=True), events)
    assert res.rows_in == n_in, "reconciliation failed: rows_in != clean + quarantined"
    return res


def validate_f2(raw: pd.DataFrame, run_id: str) -> Result:
    src = "au10y"
    df = raw.copy().reset_index(drop=True)
    n_in = len(df)
    events: list[dict] = []
    df["trade_date"] = pd.to_datetime(df["raw_date"], format="%d-%b-%Y", errors="coerce")
    blank = df["raw_value"].fillna("").str.strip() == ""
    df["value_pct"] = pd.to_numeric(df["raw_value"].where(~blank), errors="coerce")
    df["reason"] = ""

    # DQ01 interpretability: date parses; a non-blank value is numeric
    bad_date = df["trade_date"].isna()
    bad_value = ~bad_date & ~blank & df["value_pct"].isna()
    df.loc[bad_date, "reason"] = "DQ01: date does not parse as DD-Mon-YYYY"
    df.loc[bad_value, "reason"] = "DQ01: value is not a number"
    rejected = bad_date | bad_value
    # DQ02 uniqueness: one value per business date
    dup = ~rejected & df.duplicated("trade_date", keep="first")
    df.loc[dup, "reason"] = "DQ02: duplicate date"
    rejected = rejected | dup

    quarantine = df[rejected].copy()
    for _, r in quarantine.iterrows():
        events.append(_event(run_id, src, r["raw_date"], r["reason"][:4], r["reason"]))

    clean = df[~rejected].sort_values("trade_date").copy()
    clean["trade_date_syd"] = clean["trade_date"].dt.strftime("%Y-%m-%d")  # a Sydney business date; no time attached
    clean["dq_flags"] = ""
    # DQ04 completeness: blank value kept as missing and flagged, never filled
    missing = clean["value_pct"].isna()
    _add_flag(clean, missing, "DQ04")
    for _, r in clean[missing].iterrows():
        events.append(_event(run_id, src, r.trade_date_syd, "DQ04", "no yield published for this date"))
    # DQ05 accuracy: move vs previous published value within 25 bp
    prev = clean["value_pct"].ffill().shift(1)
    jump = (clean["value_pct"] - prev).abs() > 0.25
    _add_flag(clean, jump, "DQ05")
    for i, r in clean[jump].iterrows():
        events.append(_event(run_id, src, r.trade_date_syd, "DQ05",
                             f"move {(r.value_pct - prev[i]) * 100:+.1f} bp"))

    res = Result(src, clean[["trade_date_syd", "value_pct", "dq_flags"]].reset_index(drop=True),
                 quarantine[["raw_date", "raw_value", "reason"]].reset_index(drop=True), events)
    assert res.rows_in == n_in, "reconciliation failed: rows_in != clean + quarantined"
    return res
