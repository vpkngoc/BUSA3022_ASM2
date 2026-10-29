# Contributing

These rules apply equally to code written by people and code written by the AI agent.

## Workflow

1. Branch from `main`: `feat/…`, `fix/…`, `docs/…`, `chore/…`.
2. Open a pull request using the template. Nothing is pushed straight to `main`, with one exception: the scheduled `ingest` workflow (pipeline-bot) commits new files under `data/` only.
3. Every PR needs passing checks (tests and data contract) and **one approving review from a team member who did not write it**.
4. Changes drafted by the AI agent carry the `ai-assisted` label and must link the requirement they implement (for example a section of `docs/METRICS.md`).
5. The reviewer checks AI-assisted code against at least one hand-worked example, not just that it runs.

## Standards

| Area | Rule |
| --- | --- |
| Names | `snake_case` for files, columns and functions |
| Units | Suffix every measure with its unit: `_pct`, `_bp`, `_ann_pct`, `_pts` |
| Time | Instants stored as `*_utc`; business dates as `trade_date_syd`; availability as `available_from_syd`. Never take a date from a UTC timestamp without converting to `Australia/Sydney` first |
| Raw data | Write-once. Transformation code reads raw and never writes to it |
| Bad records | Never dropped silently: quarantine with a rule ID and reason |
| Secrets | None needed today; if one is ever added it goes in GitHub Secrets, never in a file |
| Metric changes | Version note in `docs/METRICS.md` and an entry in `CHANGELOG.md` |
| Grain | The daily analytical dataset keeps at most one row per ASX trading date. Completed sessions are used for completed-session metrics, while the current in-progress session may remain in the table with an explicit status flag. Duplicate trading dates are not allowed. |
| Missing values | Missing source observations remain explicitly missing and are flagged. We do not silently fill or remove missing values simply to create a complete-looking series. |
| Point in time | A value may only be used if it was available by the 6:00 pm Sydney review time. available_from_syd is retained so later RBA releases are not treated as if they were known earlier. |
| Provisional data | `provisional` and `in_progress` are treated differently. A `provisional` row represents a completed trading session whose close is usable even if another field, such as volume, is not yet final. An `in_progress` row represents a session that is still trading and is excluded from MA20, volatility and other completed-session metrics until the session closes. |
| Enforcement | These modelling rules are enforced through automated tests, including tests/test_serve_contract.py, as well as peer review before changes are merged. Documentation alone is not treated as sufficient control. |

## Recording AI errors

If a review or test catches a mistake in AI-assisted code, add a dated entry to `docs/AI_LOG.md` in the same PR.
