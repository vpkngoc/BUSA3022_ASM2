"""Paths and configuration shared by the pipeline."""
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
DATA = ROOT / "data"
RAW = DATA / "raw"
CURATED = DATA / "curated"
QUALITY = DATA / "quality"
SYD = ZoneInfo("Australia/Sydney")


def sources() -> dict:
    return yaml.safe_load((CONFIG / "sources.yaml").read_text())


def dq_rules() -> dict:
    """Rule ID -> rule dict."""
    return {r["id"]: r for r in yaml.safe_load((CONFIG / "dq_rules.yaml").read_text())["rules"]}
