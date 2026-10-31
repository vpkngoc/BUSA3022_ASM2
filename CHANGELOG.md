# Changelog

## 2026-11-01 (Part 3, dashboard v4)
- Prompt v4 (`docs/prompts/dashboard_v4.md`, supplied by Ngoc): a new one-screen 16:9 executive view, `docs/dashboard/executive.html` (designed at 1920 × 1080, no vertical scroll): header with title, period takeaway and freshness; the RAG card beside the session strip and four KPIs; ASX close and volume with the triggered sessions; yield, rolling correlation and scatter. The detailed scrollable view stays at `docs/dashboard/index.html`, and the two link to each other.
- Both views are built from one shared stylesheet and script (`dashboard/common.css`, `dashboard/common.js`), so data, calculations, thresholds and wording cannot drift apart.
- Colour system with three separate contexts: market direction (green up, red down: candles, ASX daily and period change); monitoring (Green/Amber/Red/grey: RAG card, strip, chips, volume bars, triggered sessions); analytical series (blue ASX, bluer teal `#16a6b6` for averages, normal and fitted line, true orange yield, purple correlation, grey for pending and awaiting RBA). Yield moves and the gap to the 20-session average are no longer judged by colour.
- Grey dashed "awaiting RBA release" band; non-causal correlation notes; "association" in the scatter text; compact neutral ticker; selective table colours.
- No change to data, calculations, thresholds, point-in-time logic or values.

## 2026-10-31 (Part 3, dashboard v3)
- Prompt v3 (`docs/prompts/dashboard_v3.md`) from Maika's fresh-eyes review and `docs/STYLE_GUIDE.md`: arrow = direction, colour = interpretation (index, average and yield changes neutral; volatility green or red with "Lower/Higher concern"; volume vs normal in its RAG colour with "Amber"/"Red alert"); neutral baseline shading and hollow/filled candles; reference lines in teal, ASX blue shifted to keep them apart; every change labelled with its window; "Latest completed signal" vs "Latest ASX session … not yet included"; Maika's correlation wording, computed for the selected period.
- The rolling correlation is blank on sessions whose RBA yield is not yet published.

## 2026-10-30 (Part 3, dashboard v2)
- Prompt v2 (`docs/prompts/dashboard_v2.md`) from Ngoc's critique of v1: navy theme with a new accent blue; blue ticker; "View period" label; one dense insight line under each "Show analysis"; the volume signal card leads with the RAG colour, its meaning and M4's action, with a threshold ladder; a session strip replaces the donut; aqua and violet lines instead of grey; optional candlestick view (not the default); the "awaiting RBA release" band in the yield's orange; Red days labelled on the volume chart.
- The signal follows M4 as written in `docs/METRICS.md` v1.2: Red is +60% or more only (the draft three-Ambers-in-a-row rule is removed); a zero-volume session is Excluded, not Pending.

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
