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

## Recording AI errors

If a review or test catches a mistake in AI-assisted code, add a dated entry to `docs/AI_LOG.md` in the same PR.
