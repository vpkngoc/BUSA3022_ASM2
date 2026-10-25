"""Guards on the configuration that every later stage depends on."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = {"accuracy", "completeness", "consistency", "uniqueness", "timeliness", "interpretability"}
ACTIONS = {"reject", "flag", "stop", "alert"}


def load(name):
    return yaml.safe_load((ROOT / "config" / name).read_text())


def test_exactly_two_sources_one_macro_one_index():
    sources = load("sources.yaml")
    assert sorted(s["role"] for s in sources.values()) == ["macro", "market_index"]


def test_rba_series_selected_by_id():
    au10y = load("sources.yaml")["au10y"]
    assert au10y["series_id"] == "FCMYGBAG10D"
    assert au10y["expected_units"] == "Per cent per annum"


def test_asx_timestamps_declared_as_utc_with_sydney_exchange_zone():
    asx = load("sources.yaml")["asx200"]
    assert asx["timestamp_kind"] == "utc_instant"
    assert asx["exchange_timezone"] == "Australia/Sydney"


def test_every_dq_rule_has_unique_id_known_dimension_and_one_action():
    rules = load("dq_rules.yaml")["rules"]
    ids = [r["id"] for r in rules]
    assert len(ids) == len(set(ids))
    for r in rules:
        assert r["dimension"] in DIMENSIONS, r["id"]
        assert r["action"] in ACTIONS, r["id"]
