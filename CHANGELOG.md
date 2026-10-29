# Changelog

## 2026-10-29 (Part 2)
- Metrics `ma20_pts`, `vol20_ann_pct`, `yield_change_5obs_bp` as defined by the team in `docs/METRICS.md` (commit 9831fb1) (`pipeline/metrics.py`).
- Every session with no same-dated RBA yield is flagged `rba:DQ04` and left blank (METRICS.md, M3 edge cases).
- Serve table `data/serve/daily_panel.csv`: one row per ASX session in Sydney; RBA yield joined point in time ("as at" 6:00 pm Sydney), with its age in sessions; same-day yield kept separately for analysis (`pipeline/align.py`), rebuilt after every real run.
- Data quality: the newest ASX session's live bar is labelled `provisional` (volume NULL) or `in_progress` (left out of metrics); a changed close on replacement is logged as DQ08 (DQ08 now covers both sources).
- New RBA values are available from the file's publication time, not the download time (scheduled runs started 6–7 hours late on 26–28 Oct).
- Data dictionary; serve-table contract tests enforce the modelling standards.

## 2026-10-25 (Part 1 fixes)
- `late` and `schema` simulations replay the last good raw snapshot instead of calling the provider (the first `schema` demo on GitHub never reached the schema check because the RBA returned HTTP 403).
- HTTP 403 is retried with backoff; two consecutive *stale* real runs now raise an alert, like two *late* runs.
- Workflow files are linted in CI (actionlint).

## 2026-10-25 (Part 1)
- Pipeline: Yahoo ASX 200 and RBA F2 ingestion with retry/backoff, write-once raw snapshots with manifests, rules DQ01–DQ08, quarantine, run log, F2 vintages with availability dates, release-calendar timeliness check, schema guard, failure simulations, scheduled workflow, runbook.
- DQ01, DQ02 and DQ05 now apply to both sources; `tzdata` added so Sydney time zone handling works on Windows.

## 2026-10-25
- Repository scaffold: layout, charter, contributing rules, PR template, CI, source and data quality configuration, metric requirements template.

## 29 October 2026 — Part 2 metric specification v1.1:
Clarified the 6:00 pm Sydney review point, sample-standard-deviation convention for realised volatility, 0.1 bp display rounding for yield change, completed-session treatment, and metric benchmark interpretation. Confirmed that AI-assisted transformation code must follow the committed human-approved specification.

---

## `docs/AI_LOG.md` — completed schema-change incident

### Yahoo schema change — validation stopped before logging and quarantine

- **What the AI-assisted implementation initially did:**  
  The initial parser correctly detected that the expected Yahoo `close` field was missing and raised a `SchemaError`.

- **What was incomplete:**  
  Although the schema change was detected, the exception occurred before the failure was recorded and quarantined under the required data-quality control. The pipeline therefore stopped correctly, but the failure was not yet fully observable or auditable.

- **How we identified it:**  
  A controlled pytest deliberately replaced the expected `close` field with `close_changed`. Before the correction, the focused test run produced **1 failed and 1 passed**, showing that detection worked but the required logging and quarantine behaviour did not.

- **Fix:**  
  The failure sequence was revised so the Yahoo schema change is logged and quarantined as DQ07 before the load stops. The correction was reviewed and merged through **PR #8**.

- **Verification after the fix:**  
  Re-running the focused schema tests produced **2 passed**, and the full test suite subsequently produced **30 passed**.

- **Lesson / guardrail:**  
  AI-generated validation code should not be accepted simply because it detects an error or raises an exception. Our tests must also verify the surrounding governance requirements, including logging, quarantine and auditability.