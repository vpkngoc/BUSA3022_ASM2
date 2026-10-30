# Changelog

## 2026-10-30 (Part 3, dashboard v1)
- Prompt v1 (`docs/prompts/dashboard_v1.md`) from Ngoc's critique of v0: dark theme; general title with a takeaway box; running ticker with "last fetch"; 1W / 1M / 3M (default, the brief's 90 days) / 1Y range buttons; gauge and donut for the volume signal; ▲/▼ good/bad colour on changes; descriptive titles with "Show analysis"; baseline chart for price; triggered sessions beside the volume chart; correlation as an area plus a return-vs-yield-change scatter; notes list only the data sources.
- The page now carries one year of sessions; range summaries are computed in the page. Prompt iterations logged in `docs/AI_LOG.md`.

## 2026-10-30 (Part 3, dashboard v0)
- Dashboard v0 (`dashboard/`), built by the AI agent from its own reading of the brief as the baseline for reverse prompt engineering: prompt in `docs/prompts/dashboard_v0.md`, element list in `docs/prompts/dashboard_v0_elements.md`.
- Output `docs/dashboard/index.html`, rebuilt by the nightly ingest workflow after each real run.
- Draft volume signal (M4: volume vs its 20-session normal, Green/Amber/Red/Pending), not yet in `docs/METRICS.md`; tests in `tests/test_dashboard.py`.

## 2026-10-29 (Part 2)
- Metrics `ma20_pts`, `vol20_ann_pct`, `yield_change_5obs_bp` as defined by the team in `docs/METRICS.md` (commit 9831fb1) (`pipeline/metrics.py`).
- Every session with no same-dated RBA yield is flagged `rba:DQ04` and left blank (METRICS.md, M3 edge cases).
- Serve table `data/serve/daily_panel.csv`: one row per ASX session in Sydney; RBA yield joined point in time ("as at" 6:00 pm Sydney), with its age in sessions; same-day yield kept separately for analysis (`pipeline/align.py`), rebuilt after every real run.
- Data quality: the newest ASX session's live bar is labelled `provisional` (volume NULL) or `in_progress` (left out of metrics); a changed close on replacement is logged as DQ08 (DQ08 now covers both sources).
- New RBA values are available from the file's publication time, not the download time (scheduled runs started 6–7 hours late on 26–28 Oct).
- Data dictionary; serve-table contract tests enforce the modelling standards.

## 2026-10-29 — Part 2 metric specification v1.1
- Clarified the 6:00 pm Sydney review time, sample-standard-deviation convention for realised volatility, 0.1 bp display rounding for yield change, completed-session treatment, and benchmark interpretation. Confirmed that AI-assisted transformation code must follow the committed human-approved specification.

## 2026-10-25 (Part 1 fixes)
- `late` and `schema` simulations replay the last good raw snapshot instead of calling the provider (the first `schema` demo on GitHub never reached the schema check because the RBA returned HTTP 403).
- HTTP 403 is retried with backoff; two consecutive *stale* real runs now raise an alert, like two *late* runs.
- Workflow files are linted in CI (actionlint).

## 2026-10-25 (Part 1)
- Pipeline: Yahoo ASX 200 and RBA F2 ingestion with retry/backoff, write-once raw snapshots with manifests, rules DQ01–DQ08, quarantine, run log, F2 vintages with availability dates, release-calendar timeliness check, schema guard, failure simulations, scheduled workflow, runbook.
- DQ01, DQ02 and DQ05 now apply to both sources; `tzdata` added so Sydney time zone handling works on Windows.

## 2026-10-25
- Repository scaffold: layout, charter, contributing rules, PR template, CI, source and data quality configuration, metric requirements template.
