"""Human-designed requirement (Maika): a schema failure must be OBSERVABLE, not only stop the load.

For each source, if the provider changes the format, the pipeline must
  1. stop the load (status 'stopped', nothing loaded into the clean tables),
  2. write a DQ07 event to the data quality log saying what is missing, and
  3. keep the offending snapshot in quarantine for inspection.
"""
import csv
import json
from datetime import datetime, timezone

import pytest

from pipeline import run, store
from pipeline.http import FetchResult
from tests.test_part1_pipeline import F2

NOW = datetime(2026, 10, 25, 7, 0, tzinfo=timezone.utc)

# Yahoo payload where the provider has renamed "close" (a schema change)
YAHOO_BROKEN = json.dumps({"chart": {"result": [{"meta": {}, "timestamp": [1792710000], "indicators": {"quote": [
    {"open": [8800.0], "high": [8810.0], "low": [8790.0], "close_changed": [8795.2], "volume": [970700]}]}}]}}).encode()

# RBA file where the provider has renamed the 10-year series ID (a schema change)
F2_BROKEN = F2.replace("FCMYGBAG10D", "FCMYGBAG10X").encode()


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    for mod in (store, run):
        monkeypatch.setattr(mod, "QUALITY", tmp_path / "quality", raising=False)
        monkeypatch.setattr(mod, "QUARANTINE", tmp_path / "quarantine", raising=False)
    monkeypatch.setattr(store, "RAW", tmp_path / "raw")
    monkeypatch.setattr(store, "CURATED", tmp_path / "curated")
    return tmp_path


def serve(monkeypatch, content):
    monkeypatch.setattr(run, "fetch", lambda *a, **k: FetchResult(content, "https://provider.test", [
        {"attempt": 1, "http_status": 200, "latency_ms": 1}]))


def dq07_events(tmp_path, source):
    path = tmp_path / "quality" / "dq_events.csv"
    if not path.exists():
        return []
    return [e for e in csv.DictReader(path.open()) if e["rule_id"] == "DQ07" and e["source"] == source]


def test_yahoo_schema_failure_is_logged_before_stop(sandbox, monkeypatch):
    serve(monkeypatch, YAHOO_BROKEN)
    row = run.run_asx({"url": "https://provider.test", "exchange_timezone": "Australia/Sydney"},
                      "t", NOW, NOW, "none", None)
    assert row["status"] == "stopped"
    assert not (sandbox / "curated" / "asx200_daily.csv").exists()          # nothing loaded
    events = dq07_events(sandbox, "asx200")
    assert events and "close" in events[0]["detail"]                         # observable: says what is missing
    assert list((sandbox / "quarantine").glob("t_asx200_snapshot.*"))       # kept for inspection


def test_rba_schema_failure_is_logged_before_stop(sandbox, monkeypatch):
    serve(monkeypatch, F2_BROKEN)
    row = run.run_f2({"url": "https://provider.test", "series_id": "FCMYGBAG10D",
                      "expected_units": "Per cent per annum"}, "t", NOW, NOW, "none", None)
    assert row["status"] == "stopped"
    assert not (sandbox / "curated" / "au10y_daily.csv").exists()
    events = dq07_events(sandbox, "au10y")
    assert events and "FCMYGBAG10D" in events[0]["detail"]
    assert list((sandbox / "quarantine").glob("t_au10y_snapshot.*"))