"""Part 1 tests: release clock, schema guard, validation rules, Sydney dates, retries."""
import json
from datetime import date, datetime

import pandas as pd
import pytest
import requests

from pipeline.config import SYD
from pipeline.http import FetchError, fetch
from pipeline.ingest_rba_f2 import SchemaError, parse_f2
from pipeline.ingest_yahoo import parse_chart
from pipeline.release_calendar import expected_through, latest_release_date, release_covering
from pipeline.validate import validate_asx, validate_f2

# ---------------------------------------------------------------- release clock (knowledge clock)

def syd(*args):
    return datetime(*args, tzinfo=SYD)


@pytest.mark.parametrize("as_of, release, through", [
    (syd(2026, 10, 22, 18, 0), date(2026, 10, 16), date(2026, 10, 14)),   # Thursday evening: last week's release
    (syd(2026, 10, 23, 13, 59), date(2026, 10, 16), date(2026, 10, 14)),  # Friday before 2 pm
    (syd(2026, 10, 23, 14, 0), date(2026, 10, 23), date(2026, 10, 21)),   # Friday from 2 pm
    (syd(2026, 10, 26, 9, 0), date(2026, 10, 23), date(2026, 10, 21)),    # following Monday
])
def test_expected_through_follows_friday_release(as_of, release, through):
    assert latest_release_date(as_of) == release
    assert expected_through(as_of) == through


def test_release_covering_reconstructs_publication_time():
    assert release_covering(date(2026, 10, 21)) == syd(2026, 10, 23, 14, 0)   # Wednesday -> that Friday
    assert release_covering(date(2026, 10, 22)) == syd(2026, 10, 30, 14, 0)   # Thursday -> next Friday

# ---------------------------------------------------------------- RBA F2 parsing and schema guard

F2 = """﻿F2 CAPITAL MARKET YIELDS – GOVERNMENT BONDS
Title,Australian Government 5 year bond,Australian Government 10 year bond
Units,Per cent per annum,Per cent per annum
Publication date,23-Oct-2026,23-Oct-2026
Series ID,FCMYGBAG5D,FCMYGBAG10D
02-Oct-2026,4.300,4.950
05-Oct-2026,,
06-Oct-2026,4.310,4.990
07-Oct-2026,4.320,n/a
08-Oct-2026,4.330,5.300
"""


def test_series_selected_by_id_not_position():
    df, info = parse_f2(F2.encode(), "FCMYGBAG10D", "Per cent per annum")
    assert df.raw_value.tolist() == ["4.950", "", "4.990", "n/a", "5.300"]
    assert info["publication_date"] == "23-Oct-2026"


def test_schema_guard_stops_on_missing_series():
    with pytest.raises(SchemaError):
        parse_f2(F2.replace("FCMYGBAG10D", "FCMYGBAG10X").encode(), "FCMYGBAG10D", "Per cent per annum")


def test_schema_guard_stops_on_unit_change():
    with pytest.raises(SchemaError):
        parse_f2(F2.replace("Per cent per annum\n", "Basis points\n").encode(), "FCMYGBAG10D", "Per cent per annum")


def test_f2_rules_keep_blank_flag_jump_quarantine_garbage():
    df, _ = parse_f2(F2.encode(), "FCMYGBAG10D", "Per cent per annum")
    res = validate_f2(df, "test")
    assert res.rows_in == len(df) == 5                       # reconciliation: nothing silently dropped
    assert res.quarantine.reason.tolist() == ["DQ01: value is not a number"]
    labour_day = res.clean.set_index("trade_date_syd").loc["2026-10-05"]
    assert pd.isna(labour_day.value_pct) and "DQ04" in labour_day.dq_flags   # kept, flagged, not filled
    assert "DQ05" in res.clean.set_index("trade_date_syd").loc["2026-10-08"].dq_flags  # +31 bp jump

# ---------------------------------------------------------------- ASX: Sydney dates across daylight saving

def chart(bars):
    """bars: list of (utc_iso, close, volume)."""
    ts = [int(pd.Timestamp(b[0]).timestamp()) for b in bars]
    q = {"open": [b[1] for b in bars], "high": [b[1] for b in bars], "low": [b[1] for b in bars],
         "close": [b[1] for b in bars], "volume": [b[2] for b in bars]}
    return json.dumps({"chart": {"result": [{"meta": {"exchangeTimezoneName": "Australia/Sydney"},
                                             "timestamp": ts, "indicators": {"quote": [q]}}]}}).encode()


BARS = [
    ("2026-10-02T00:00:00Z", 8800.0, 0),        # Fri 2 Oct 10:00 AEST; zero volume
    ("2026-10-03T00:00:00Z", 8801.0, 500),      # a Saturday bar: impossible
    ("2026-10-04T23:00:00Z", 8810.0, 900),      # Mon 5 Oct 10:00 AEDT (UTC date is the 4th!)
    ("2026-10-05T23:00:00Z", 8820.0, 950),      # Tue 6 Oct 10:00 AEDT
    ("2026-10-06T05:53:00Z", 8820.0, 0),        # Tue 6 Oct 16:53 AEDT: live/partial duplicate
]


def test_trade_dates_are_sydney_dates_not_utc_dates():
    df, _ = parse_chart(chart(BARS))
    res = validate_asx(df, "test")
    assert res.clean.trade_date_syd.tolist() == ["2026-10-02", "2026-10-05", "2026-10-06"]


def test_asx_rules_reconcile_and_explain_every_rejection():
    df, _ = parse_chart(chart(BARS))
    res = validate_asx(df, "test")
    assert res.rows_in == 5 and len(res.clean) == 3 and len(res.quarantine) == 2
    reasons = " | ".join(res.quarantine.reason)
    assert "DQ01: Sydney date falls on a weekend" in reasons
    assert "DQ02: second bar for 2026-10-06 stamped 16:53" in reasons
    kept = res.clean.set_index("trade_date_syd")
    assert kept.loc["2026-10-06"].volume == 950                  # the 10:00-stamped bar is kept
    assert "DQ03" in kept.loc["2026-10-02"].dq_flags             # zero volume flagged, row kept


def test_chart_schema_guard():
    with pytest.raises(SchemaError):
        parse_chart(b'{"chart": {"result": [{"timestamp": []}]}}')

# ---------------------------------------------------------------- failure scenario: retries

class Fake:
    def __init__(self, codes):
        self.codes, self.calls = list(codes), 0

    def get(self, url, **_):
        r = requests.Response()
        r.status_code = self.codes[min(self.calls, len(self.codes) - 1)]
        r._content, r.url = (b"ok" if r.status_code == 200 else b"err"), url
        self.calls += 1
        return r


def test_retries_then_succeeds():
    waits = []
    res = fetch("https://example.test", session=Fake([429, 503, 200]), sleep=waits.append)
    assert [a["http_status"] for a in res.attempts] == [429, 503, 200]
    assert len(waits) == 2 and waits[1] > waits[0]               # growing backoff


def test_gives_up_with_full_attempt_log():
    with pytest.raises(FetchError) as exc:
        fetch("https://example.test", session=Fake([429]), sleep=lambda s: None)
    assert len(exc.value.attempts) == 4


def test_non_retryable_status_fails_fast():
    with pytest.raises(FetchError) as exc:
        fetch("https://example.test", session=Fake([404]), sleep=lambda s: None)
    assert len(exc.value.attempts) == 1
