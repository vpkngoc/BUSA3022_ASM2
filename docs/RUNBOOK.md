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
| **stale** | The source could not be reached after 4 attempts (rate limit, timeout, or the site refusing access with HTTP 403); the last good load is kept | Re-run later. If the next real run is also stale, an issue opens; check the source in a browser |
| **stopped** | The file no longer matches the data contract (series ID or units changed); nothing was loaded | Open the quarantined snapshot in `data/quarantine/`, compare it with `config/sources.yaml`, and raise a PR to update the contract **only after** confirming the change with the RBA |

**PASS / WARN / FAIL at a glance**

| Run result on GitHub | Status in the summary | What it means |
| --- | --- | --- |
| PASS: green tick | ok | Everything loaded and reconciled |
| WARN: green tick with a yellow warning | late or stale | Expected now and then; the dashboard shows "as at". No action on the first occurrence |
| FAIL: red cross and a GitHub issue | stopped or failed, or late/stale on two runs in a row | Someone must act today: follow the row for that status above |

### Where things are

| File | What it holds |
| --- | --- |
| `data/raw/<source>/<date>/<run_id>.*` | Exactly what was downloaded, never edited, with a `.manifest.json` (URL, size, SHA-256, time) |
| `data/curated/asx200_daily.csv` | One row per ASX trading day, dated in Sydney time |
| `data/curated/au10y_daily.csv` | One row per RBA date, with `available_from_syd` (when the value could first be known) |
| `data/curated/au10y_vintages.csv` | Every new or revised yield and when we first saw it |
| `data/quality/dq_run_log.csv` | One row per source per run: status, counts, expected vs received dates, fetch attempts |
| `data/quality/dq_events.csv` | Every rule that fired, on which record, and why |
| `data/quarantine/` | Rejected rows (and stopped snapshots) with their reasons |
| `config/dq_rules.yaml` | The rules DQ01–DQ08 and what each one does |

### Demonstrate the failure handling

```bash
python -m pipeline.run --simulate 429      # rate limit: 4 attempts, then the last good load is kept
python -m pipeline.run --simulate late     # the latest RBA release never arrives: status 'late'
python -m pipeline.run --simulate schema   # the RBA renames the series: load stopped, alert raised
```

Simulated runs are marked `simulated = True` in the log and never change the clean tables. The `late` and `schema` demos replay the last good raw snapshot already in the repo, so they behave the same every time and never call the RBA or Yahoo. The `429` demo uses a fake connection that always refuses.

On GitHub: Actions → **ingest** → **Run workflow** → choose the scenario. `schema` should finish with a **red ✗** and open an issue titled "Pipeline alert"; close that issue as "simulated". `late` should finish with a **green ✓ plus a yellow warning**: one late release is expected now and then, so it is shown, not escalated.

**Escalation policy:** a broken data contract (*stopped*) alerts at once. A single *late* or *stale* run does not, because the dashboard already shows "as at" and an alert on every slow RBA release would teach people to ignore alerts. The same problem on two consecutive real runs opens an issue. This rule is tested in `tests/test_simulations.py`.

### Observed in production

- **25 Oct 2026, 07:26 UTC:** the RBA site answered GitHub's runner with **HTTP 403** four minutes after a successful download. The pipeline kept the last good load and marked the source *stale*, as designed. A 403 is now retried with backoff, like a rate limit.
- **26–28 Oct 2026: the scheduled run started 6 to 7 hours late** (scheduled 07:17 UTC; started 14:19, 13:16 and 14:03 UTC, i.e. after midnight Sydney). GitHub's documentation says scheduled runs can be delayed when Actions is busy. Nothing broke, but our download time is no longer a good proxy for when the RBA published, so new RBA values are now dated from the file's own *Publication date* (2:00 pm), never later than when we saw them. If an on-time run ever matters, trigger it by hand.
- **Every weekday night: the newest ASX session arrives as a live bar** (stamped about 4:55 pm Sydney, volume 0) next to an empty 10:00 bar, which DQ01 quarantines. The next night the final bar replaces it. In the two replacements seen so far the close was unchanged; any change is now logged as DQ08.
- **29 Oct 2026, 12:20 Sydney (test run during trading):** Yahoo's bar for the previous session (28 Oct) was still empty and its live bar had gone, so a run from an empty folder would have quarantined 28 Oct (DQ01). The repository's clean table kept the provisional 28 Oct row from the night before, because an upsert only replaces dates that arrive clean. Yahoo also reported the regular session ending at 4:12 pm Sydney, which is why a live bar stamped before 4:15 pm is treated as *in_progress*.

### Known, expected flags

- **DQ04 on the first Monday of October** (NSW Labour Day): the ASX trades but the RBA publishes no yield. Kept as missing, never filled.
- **DQ05 on historic big days** (for example 19–20 March 2020): flagged for review, not removed.
- **DQ02 on the latest ASX date**: Yahoo sends a second, live bar during the day; it is quarantined and the 10:00-stamped bar is kept.
- **DQ01 + DQ03 on the newest session every night**: the empty 10:00 placeholder is quarantined (no close) and the live bar is kept with volume 0 (see "Observed in production").

## Part 2 — curation: one Sydney time axis and the metrics

### What runs

At the end of every real run, `pipeline.run` rebuilds `data/serve/daily_panel.csv` from the clean tables (simulations never touch it). To rebuild it on its own:

```bash
python -m pipeline.align
```

The run summary ends with one line such as *"Serve table rebuilt: 511 sessions, latest 2026-10-28 (provisional bar); RBA yield as at 6 pm is dated 2026-10-21 (5 sessions old)."* If it says **NOT rebuilt**, the run fails and an issue opens: the dashboard would otherwise show yesterday's numbers without saying so.

### How to read a row

Every row answers: *what could a manager know at 6:00 pm Sydney on this trading day?* Columns are described in [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md); the metric definitions are the team's, in [`METRICS.md`](METRICS.md).

| You see | It means | Do |
| --- | --- | --- |
| `yield_asat_age_sessions` 2 to 6 (1 in some holiday weeks) | Normal: the RBA publishes weekly | Show "RBA yield as at <obs date>" next to the number |
| `bar_status = provisional` | Latest session; close final, volume not yet known | Show the close; leave the volume bar empty, not zero |
| `bar_status = in_progress` | Someone ran the pipeline during trading hours | Ignore the row's close for decisions; the metrics already skip it |
| Blank `yield_same_day_pct` | Not published yet, or no RBA value that day (e.g. NSW Labour Day) | Nothing: never fill it in |

### Checks

`tests/test_metrics.py` (formulas against hand calculations), `tests/test_align.py` (point in time, daylight saving, provisional bars) and `tests/test_serve_contract.py` (modelling standards on the real data) run on every pull request.

## Part 3 — the dashboard

### Where it is

| View | File | Use it for |
| --- | --- | --- |
| Executive (16:9, one screen, designed for 1920 × 1080) | `docs/dashboard/executive.html` | The report, the presentation and the daily 30-second check |
| Detailed (scrolls) | `docs/dashboard/index.html` | Investigation: full-size charts, "Show analysis", the row-level table |

Online, once GitHub Pages is switched on (Settings → Pages → Deploy from a branch → `main`, folder `/docs`): `https://vpkngoc.github.io/BUSA3022_ASM2/dashboard/` and `.../dashboard/executive.html`. The repository must be public, or on a plan that allows Pages for private repositories.

### When it updates

The ingest workflow rebuilds both pages after every real run and commits them with the data, so the published pages follow the pipeline. Simulated runs do not rebuild them.

### Build or preview it on your computer

```bash
python -m dashboard.build     # writes both pages; open them in a browser
python -m dashboard.serve     # http://localhost:8000/dashboard/ : rebuilds and reloads the tab when you save a change
```

Change the layout in `dashboard/template.html` (detailed) or `dashboard/executive.html`; change colours, wording or charts used by both in `dashboard/common.css` and `dashboard/common.js`; change a signal rule only in `dashboard/indicators.py`, and only after `docs/METRICS.md` changes. The colour rules are in `docs/STYLE_GUIDE.md` section 4.

### Read it

| You see | It means | Do |
| --- | --- | --- |
| Large card Green | The latest **completed** session's volume was below +30% of its normal | Nothing |
| Large card Amber | +30% to below +60% | As `docs/METRICS.md` M4 says: check the ASX calendar for a known event (month end, index rebalance, derivatives expiry) and read it with M1 and M2; no escalation on its own |
| Large card Red | +60% or more | As M4 says: label the event; if no scheduled event explains it, or volatility (M2) is also elevated, add a short note for management |
| Grey "provisional" next to the latest session | Its volume is not final yet, so it is not in the signal | Nothing; it is assessed on the next run |
| Grey "Awaiting RBA release" on the yield chart | The RBA has not published those days yet (weekly, Fridays 2 pm) | Nothing; never fill it in |
| "Last data fetch" more than one working day old | The pipeline has not run | Check Actions → ingest, and the issues list |

### Checks

`tests/test_dashboard.py` covers the thresholds, Pending and Excluded, the 90-day window, the correlation on unpublished days, and that both views build from the same data, script and thresholds (and that no older layout comes back after a merge).
