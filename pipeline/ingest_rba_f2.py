"""Parse RBA Statistical Table F2 (CSV) for one series, selected by its Series ID.

The file starts with metadata rows (Title, Description, Frequency, Type, Units, Source,
Publication date, Series ID) before the data. Columns are found by Series ID, never by
position, and the units are checked against the data contract (DQ07 schema guard).
"""
from __future__ import annotations

import csv
import io

import pandas as pd


class SchemaError(Exception):
    """The file no longer matches the data contract: stop the load (DQ07)."""


def _row(rows: list[list[str]], label: str) -> list[str] | None:
    return next((r for r in rows if r and r[0].strip() == label), None)


def parse_f2(raw: bytes, series_id: str, expected_units: str) -> tuple[pd.DataFrame, dict]:
    text = raw.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    header_idx = next((i for i, r in enumerate(rows) if r and r[0].strip() == "Series ID"), None)
    if header_idx is None:
        raise SchemaError("'Series ID' header row not found")
    ids = [c.strip() for c in rows[header_idx]]
    if series_id not in ids:
        raise SchemaError(f"series {series_id} not found in the Series ID row")
    col = ids.index(series_id)

    units_row = _row(rows[:header_idx], "Units")
    units = units_row[col].strip() if units_row and len(units_row) > col else None
    if units != expected_units:
        raise SchemaError(f"units for {series_id} are {units!r}, expected {expected_units!r}")

    def meta(label):
        r = _row(rows[:header_idx], label)
        return r[col].strip() if r and len(r) > col else None

    records = [
        {"raw_date": r[0].strip(), "raw_value": (r[col].strip() if len(r) > col else "")}
        for r in rows[header_idx + 1:]
        if r and r[0].strip()
    ]
    info = {"title": meta("Title"), "units": units, "publication_date": meta("Publication date"),
            "source": meta("Source"), "series_id": series_id}
    return pd.DataFrame(records, columns=["raw_date", "raw_value"]), info
