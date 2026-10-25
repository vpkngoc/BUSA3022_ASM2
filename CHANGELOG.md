# Changelog

## 2026-10-25 (Part 1 fixes)
- `late` and `schema` simulations replay the last good raw snapshot instead of calling the provider (the first `schema` demo on GitHub never reached the schema check because the RBA returned HTTP 403).
- HTTP 403 is retried with backoff; two consecutive *stale* real runs now raise an alert, like two *late* runs.
- Workflow files are linted in CI (actionlint).

## 2026-10-25 (Part 1)
- Pipeline: Yahoo ASX 200 and RBA F2 ingestion with retry/backoff, write-once raw snapshots with manifests, rules DQ01–DQ08, quarantine, run log, F2 vintages with availability dates, release-calendar timeliness check, schema guard, failure simulations, scheduled workflow, runbook.
- DQ01, DQ02 and DQ05 now apply to both sources; `tzdata` added so Sydney time zone handling works on Windows.

## 2026-10-25
- Repository scaffold: layout, charter, contributing rules, PR template, CI, source and data quality configuration, metric requirements template.
