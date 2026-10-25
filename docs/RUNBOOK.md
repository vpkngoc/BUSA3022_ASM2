# Runbook

Written so a team member who did not build the pipeline can run it, read its results and act on them without help. If anything here is unclear, write it down: that feedback is how this page improves.

## Part 1 — the pipeline

### What runs, and when

| What | When | Where |
| --- | --- | --- |
| Download ASX 200 daily bars (Yahoo) and RBA Table F2 | Weekdays 07:17 UTC (17:17–18:17 Sydney, after the ASX close) | GitHub → **Actions** → **ingest** |
| Tests | Every pull request | GitHub → **Actions** → **ci** |

The RBA publishes F2 **weekly, on Fridays at 2:00 pm**, covering yields up to two business days earlier (usually Wednesday). Monday to Thursday, the newest yield is therefore always several days old. That is normal, not an error.

### Run it by hand

**On GitHub (no install):** Actions → **ingest** → **Run workflow** → choose `none` → **Run workflow**. When it finishes, open the run: the summary table is shown at the bottom of the page.

**On your computer (VS Code terminal):**

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pipeline.run
pytest -q
```

### Read the result

Open `data/quality/last_run_summary.md` (or the Actions run summary). For each source:

| Status | Meaning | What to do |
| --- | --- | --- |
| **ok** | Loaded. `in = clean + quarantined` | Nothing |
| **late** | F2 has not reached the date the release calendar expects | Nothing on the first day: the dashboard shows "as at". If it is still late on the next run, an issue opens; check the RBA site |
| **stale** | The source could not be reached after 4 attempts; the last good load is kept | Re-run later. If it repeats, check the source in a browser |
| **stopped** | The file no longer matches the data contract (series ID or units changed); nothing was loaded | Open the quarantined snapshot in `data/quality/quarantine/`, compare it with `config/sources.yaml`, and raise a PR to update the contract **only after** confirming the change with the RBA |

### Where things are

| File | What it holds |
| --- | --- |
| `data/raw/<source>/<date>/<run_id>.*` | Exactly what was downloaded, never edited, with a `.manifest.json` (URL, size, SHA-256, time) |
| `data/curated/asx200_daily.csv` | One row per ASX trading day, dated in Sydney time |
| `data/curated/au10y_daily.csv` | One row per RBA date, with `available_from_syd` (when the value could first be known) |
| `data/curated/au10y_vintages.csv` | Every new or revised yield and when we first saw it |
| `data/quality/dq_run_log.csv` | One row per source per run: status, counts, expected vs received dates, fetch attempts |
| `data/quality/dq_events.csv` | Every rule that fired, on which record, and why |
| `data/quality/quarantine/` | Rejected rows (and stopped snapshots) with their reasons |
| `config/dq_rules.yaml` | The rules DQ01–DQ08 and what each one does |

### Demonstrate the failure handling

```bash
python -m pipeline.run --simulate 429      # rate limit: 4 attempts, then the last good load is kept
python -m pipeline.run --simulate late     # the latest RBA release never arrives: status 'late'
python -m pipeline.run --simulate schema   # the RBA renames the series: load stopped, alert raised
```

Simulated runs are marked `simulated = True` in the log and never change the clean tables.

### Known, expected flags

- **DQ04 on the first Monday of October** (NSW Labour Day): the ASX trades but the RBA publishes no yield. Kept as missing, never filled.
- **DQ05 on historic big days** (for example 19–20 March 2020): flagged for review, not removed.
- **DQ02 on the latest ASX date**: Yahoo sends a second, live bar during the day; it is quarantined and the 10:00-stamped bar is kept.
