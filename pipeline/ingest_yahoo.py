"""Parse a Yahoo Finance chart-endpoint payload for one index into one row per bar.

Yahoo stamps each daily bar with a UTC instant (the session open, 10:00 Sydney). The
trading date is derived later by converting to Australia/Sydney, never from the UTC date.
"""
from __future__ import annotations

import json

import pandas as pd

from .ingest_rba_f2 import SchemaError


def parse_chart(raw: bytes) -> tuple[pd.DataFrame, dict]:
    try:
        payload = json.loads(raw)
        result = payload["chart"]["result"][0]
        quote = result["indicators"]["quote"][0]
        stamps = result["timestamp"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise SchemaError(f"chart payload missing expected fields: {exc}") from exc
    for field in ("open", "high", "low", "close", "volume"):
        if field not in quote:
            raise SchemaError(f"chart payload missing '{field}'")
    df = pd.DataFrame({
        "epoch_s": stamps,
        "open": quote["open"], "high": quote["high"], "low": quote["low"],
        "close": quote["close"], "volume": quote["volume"],
    })
    meta = result.get("meta", {})
    info = {"symbol": meta.get("symbol"), "exchange_timezone": meta.get("exchangeTimezoneName"),
            "currency": meta.get("currency")}
    return df, info
