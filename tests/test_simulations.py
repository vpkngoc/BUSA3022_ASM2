"""Failure demos must not depend on the network: they replay the last good raw snapshot."""
from datetime import datetime, timezone

import pytest

from pipeline import run, store
from pipeline.config import SYD
from pipeline.http import fetch
from tests.test_part1_pipeline import F2, Fake


class NoNetwork:
    def get(self, *_, **__):
        raise AssertionError("a simulation must not call the provider")


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    raw, curated, quality = tmp_path / "raw", tmp_path / "curated", tmp_path / "quality"
    for mod in (store, run):
        monkeypatch.setattr(mod, "QUALITY", quality, raising=False)
        monkeypatch.setattr(mod, "QUARANTINE", tmp_path / "quarantine", raising=False)
    monkeypatch.setattr(store, "RAW", raw)
    monkeypatch.setattr(store, "CURATED", curated)
    snap = raw / "au10y" / "2026-10-25"
    snap.mkdir(parents=True)
    (snap / "20261025T000000Z.csv").write_bytes(F2.encode())
    return tmp_path


CFG = {"url": "https://example.test/f2.csv", "series_id": "FCMYGBAG10D", "expected_units": "Per cent per annum"}
NOW = datetime(2026, 10, 25, 7, 0, tzinfo=timezone.utc)


def test_schema_simulation_stops_without_network(sandbox):
    row = run.run_f2(CFG, "t-simschema", NOW, NOW, "schema", NoNetwork())
    assert row["status"] == "stopped"
    assert "DQ07" in row["detail"] and "replayed" in row["detail"]


def test_late_simulation_reports_late_without_network(sandbox):
    as_of = datetime(2026, 10, 16, 18, 0, tzinfo=SYD)   # Friday after release: expected through Wed 14 Oct
    row = run.run_f2(CFG, "t-simlate", NOW, as_of, "late", NoNetwork())
    assert row["status"] == "late"
    assert row["received_through"] < row["expected_through"]


def test_forbidden_is_retried_like_a_rate_limit():
    res = fetch("https://example.test", session=Fake([403, 403, 200]), sleep=lambda s: None)
    assert [a["http_status"] for a in res.attempts] == [403, 403, 200]


# ---------------------------------------------------------------- escalation policy

def rows(*pairs):
    return [{"source": "au10y", "status": s, "previous_status": p} for s, p in pairs]


@pytest.mark.parametrize("current, previous, simulate, alert", [
    ("late", "ok", "none", False),       # first late release: show 'as at', no alarm
    ("late", "late", "none", True),      # late twice in a row: escalate
    ("stale", "stale", "none", True),    # unreachable twice in a row: escalate
    ("late", "late", "late", False),     # demos never escalate
    ("stopped", "ok", "schema", True),   # broken contract: alert at once, even in a demo
    ("ok", "late", "none", False),
])
def test_escalation_policy(current, previous, simulate, alert):
    assert run.needs_alert(rows((current, previous)), simulate) is alert
