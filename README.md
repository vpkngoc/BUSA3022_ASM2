# Market Intelligence Analytics: ASX 200 and Australia's long-term borrowing rate

BUSA3022 Managing Analytics and Algorithmic Systems — Assessment 2, Analytics Lead Case Study (Really Big Bank, post-trade team).

> **Status (1 Nov 2026):** all three proof-of-concept parts are built and tested. Part 1 pipeline (scheduled ingestion, raw/quarantine/curated storage, quality log, failure handling), Part 2 curation (the team's three metrics on one Sydney time axis, point in time), Part 3 dashboard (executive 16:9 view and detailed view, volume signal, macro overlay). Figures quoted in the report: [`docs/evidence/figures_2026-10-30.md`](docs/evidence/figures_2026-10-30.md).

## The business question

*How has market activity trended over the past 90 days, and is there anything we should be watching?* — for financially literate, non-technical post-trade managers, so that bank performance can eventually be benchmarked against industry data.

## Data sources (two, as the brief requires)

| Role | Series | Provider | Notes |
| --- | --- | --- | --- |
| Market index | S&P/ASX 200 (`^AXJO`), daily OHLCV | Yahoo Finance chart endpoint | Timestamps are UTC instants; converted to Sydney trading dates |
| Macro series | Australian Government 10-year bond yield (`FCMYGBAG10D`) | RBA Statistical Table F2 | The RBA's assessment of closing yields; released weekly (Fridays 2:00 pm, data up to 2 business days earlier) |

See [`docs/DATA_USE.md`](docs/DATA_USE.md) for how each source may and may not be used, and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the parts fit together.

## Repository layout

```
pipeline/     Part 1 — ingestion, validation, quality logging
              Part 2 — metrics.py (the three metrics), align.py (Sydney time axis, serve table)
dashboard/    Part 3 — indicators.py (volume signal, correlation), build.py, two page templates
              sharing common.css/common.js, serve.py (local preview); output in docs/dashboard/
analysis/     Scripts that recompute the figures quoted in the report (evidence pack)
config/       Source definitions (data contract) and data quality rules
data/         raw (write-once snapshots) → curated → serve, plus quality logs
tests/        Automated checks run on every pull request
docs/         Charter, metrics, architecture, data dictionary, data use, runbook, style guide,
              AI log and dashboard prompts (docs/prompts/), evidence, the published dashboard
```

## How to run (local, VS Code or terminal)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
python -m pipeline.run                   # Parts 1–2: download, check, store, then rebuild data/serve
python -m pipeline.align                 # Part 2 only: rebuild data/serve/daily_panel.csv
python -m dashboard.build                # Part 3: write docs/dashboard/index.html and executive.html
python -m dashboard.serve                # Part 3: preview on http://localhost:8000/dashboard/ (reloads on save)
python analysis/evidence_pack.py         # recompute the figures the report quotes
python -m pipeline.run --simulate late   # demo a failure: also 429 or schema
```

Read the result in `data/quality/last_run_summary.md`. The full guide is [`docs/RUNBOOK.md`](docs/RUNBOOK.md).

## Team and AI use

- Team: Ngoc and Maika (co-leads; see [`docs/CHARTER.md`](docs/CHARTER.md)).
- AI agent: Claude (Anthropic) was used to draft code, tests, configuration and repository documentation. Every AI-assisted change arrives as a pull request labelled `ai-assisted` and is reviewed by a team member before merge. Errors found in AI output are recorded in [`docs/AI_LOG.md`](docs/AI_LOG.md).
- The report text is written by the team; any generative-AI text quoted in it is cited (APA 7).

## Links

- Dashboard, executive view (16:9): <https://vpkngoc.github.io/BUSA3022_ASM2/dashboard/executive.html>
- Dashboard, detailed view: <https://vpkngoc.github.io/BUSA3022_ASM2/dashboard/>
  (live once GitHub Pages is switched on: Settings → Pages → `main`, `/docs`; until then open the files in `docs/dashboard/`)
- Report: *(submitted via iLearn/Turnitin)*
- Presentation video: *TBC*
