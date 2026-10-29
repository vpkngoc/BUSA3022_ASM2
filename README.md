# Market Intelligence Analytics: ASX 200 and Australia's long-term borrowing rate

BUSA3022 Managing Analytics and Algorithmic Systems — Assessment 2, Analytics Lead Case Study (Really Big Bank, post-trade team).

> **Status:** Part 1 pipeline and Part 2 curation built (scheduled ingestion, quality log, failure handling; metrics on one Sydney time axis). Dashboard proof of concept is next.

## The business question

*How has market activity trended over the past 90 days, and is there anything we should be watching?* — for financially literate, non-technical post-trade managers, so that bank performance can eventually be benchmarked against industry data.

## Data sources (two, as the brief requires)

| Role | Series | Provider | Notes |
| --- | --- | --- | --- |
| Market index | S&P/ASX 200 (`^AXJO`), daily OHLCV | Yahoo Finance chart endpoint | Timestamps are UTC instants; converted to Sydney trading dates |
| Macro series | Australian Government 10-year bond yield (`FCMYGBAG10D`) | RBA Statistical Table F2 | The RBA's assessment of closing yields; released weekly (Fridays 2:00 pm, data up to 2 business days earlier) |

See [`docs/DATA_USE.md`](docs/DATA_USE.md) (to come) for how each source may and may not be used.

## Repository layout

```
pipeline/     Part 1 — ingestion, validation, quality logging
              Part 2 — metrics.py (the three metrics), align.py (Sydney time axis, serve table)
dashboard/    Part 3 — dashboard build (Python/Plotly) published to GitHub Pages
notebooks/    Walkthroughs for markers (Colab / VS Code)
config/       Source definitions, data quality rules, metric definitions
data/         raw (write-once snapshots) → curated → serve, plus quality logs
tests/        Automated checks run on every pull request
docs/         Charter, metric requirements, runbook, style guide, AI log
```

## How to run (local, VS Code or terminal)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
python -m pipeline.run                   # Parts 1–2: download, check, store, then rebuild data/serve
python -m pipeline.align                 # Part 2 only: rebuild data/serve/daily_panel.csv
python -m pipeline.run --simulate late   # demo a failure: also 429 or schema
```

Read the result in `data/quality/last_run_summary.md`. The full guide is [`docs/RUNBOOK.md`](docs/RUNBOOK.md).

## Team and AI use

- Team: Ngoc and Maika (co-leads; see [`docs/CHARTER.md`](docs/CHARTER.md)).
- AI agent: Claude (Anthropic) was used to draft code, tests, configuration and repository documentation. Every AI-assisted change arrives as a pull request labelled `ai-assisted` and is reviewed by a team member before merge. Errors found in AI output are recorded in [`docs/AI_LOG.md`](docs/AI_LOG.md).
- The report text is written by the team; any generative-AI text quoted in it is cited (APA 7).

## Links (added at submission)

- Report: *(submitted via iLearn/Turnitin)*
- Presentation video: *TBC*
- Dashboard: *TBC*
