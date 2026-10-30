# AI agent log

Every entry is a real event, dated, and written by the team member who observed it. Nothing here is staged or invented.

The log supports three rubric points: a specific example of incorrect or incomplete agent output and how it was caught; evidence of prompt iteration for the audience; and the reflection on what worked and what did not.

## Entry format

```
### YYYY-MM-DD — short title
- Who noticed:
- Part (1 pipeline / 2 curation / 3 dashboard):
- What the agent produced:
- What was wrong or incomplete:
- How we found it (test, hand check, review):
- Fix and follow-up (PR link):
- Lesson / guardrail added:
```

## Prompt iterations (Part 3)

| Version | Prompt (verbatim) | What the output got wrong for the audience | Screenshot |
| v0 | agent-written baseline, see docs/prompts/dashboard_v0.md | --- | --- |

## Entries
### 2026-10-25 — Workflow file could not be parsed
- Who noticed: Ngoc, on the GitHub Actions page
- Part: 1 (pipeline)
- What the agent produced: a scheduled workflow (`.github/workflows/ingest.yml`) for daily ingestion
- What was wrong: the alert step contained `Pipeline alert: …` unquoted; in YAML a colon followed by a space starts a new key, so GitHub could not read the file. The workflow showed as a file path instead of "ingest" and recorded a failed run on every push
- How we found it: the Actions list showed `ingest.yml` failing on pushes it was never meant to run on
- Fix and follow-up: PR #3 (command rewritten as a block)
- Lesson / guardrail added: CI now runs `actionlint` on every pull request, so an invalid workflow file can no longer be merged

### 2026-10-25 — Failure demo depended on a live website
- Who noticed: Ngoc, from the run summary of `ingest #5` (simulate = schema)
- Part: 1 (pipeline)
- What the agent produced: a `--simulate schema` demo that downloaded the RBA file and then renamed the series to trigger the schema guard
- What was wrong: the RBA site returned HTTP 403 to GitHub's runner, so the download failed before the schema check. The run ended "stale" and the demo showed nothing
- How we found it: the summary showed au10y = stale with "HTTP 403", not stopped
- Fix and follow-up: PR #4. Simulations now replay the last good raw snapshot; HTTP 403 is retried with backoff; two consecutive stale runs raise an alert. Re-run `ingest #6` showed au10y = stopped (DQ07) and opened issue #5
- Lesson / guardrail added: tests now fail if a simulation calls the network. The 403 itself was a real production failure, and the designed fallback (keep the last good load, mark it stale) handled it

### 2026-10-25 — "Tests pass" was only true on the agent's machine
- Who noticed: the CI check on PR #2 (red ✗), confirmed by Ngoc
- Part: 1 (pipeline)
- What the agent produced: pipeline code and tests, reported as "19 passed"
- What was wrong: the agent ran `python -m pytest`, which adds the repo folder to Python's path; CI runs plain `pytest`, which does not, so the tests could not import the code
- How we found it: CI failed on the first push of PR #2
- Fix and follow-up: PR #2, commit "fix(ci)…" (pytest path set in `pyproject.toml`)
- Lesson / guardrail added: a result only counts when CI passes, not when the agent says it passed

### 2026-10-25 — Two bugs the agent caught in its own test runs
- Who noticed: Claude, while running the pipeline before opening PR #2 (verified by Ngoc in the PR description)
- Part: 1 (pipeline)
- What was wrong: (1) the first-ever run crashed (`KeyError: dq_flags`) because the empty starting table lacked a column; (2) the "keep the last good load" fallback searched for `*.json` and picked the manifest file instead of the data snapshot
- How we found it: running the pipeline end to end, and reading the 429 demo's output path
- Fix and follow-up: fixed in `pipeline/store.py` before PR #2 was opened
- Lesson / guardrail added: run the whole pipeline from an empty state before review, not just the unit tests

### 2026-10-25 — Yahoo schema change stopped the run but was not logged
- Who noticed: Maika (requirement and test design); gap confirmed by her test failing in CI
- Part: 1 (pipeline)
- What the AI-assisted implementation initially did:
  The initial parser correctly detected that the expected Yahoo `close` field was missing and raised a `SchemaError`.
- What was incomplete:
  Although the schema change was detected, the exception occurred before the failure was recorded and quarantined under the required data-quality control. The pipeline therefore stopped correctly, but the failure was not yet fully observable or auditable.
- How we identified it:
  A controlled pytest deliberately replaced the expected `close` field with `close_changed`. Before the correction, the focused test run produced **1 failed and 1 passed**, showing that detection worked but the required logging and quarantine behaviour did not.
- Fix:
  The failure sequence was revised so the Yahoo schema change is logged and quarantined as DQ07 before the load stops. The correction was reviewed and merged through **PR #8**.
- Verification after the fix:
  Re-running the focused schema tests produced **2 passed**, and the full test suite subsequently produced **30 passed**.
- Lesson / guardrail:
  AI-generated validation code should not be accepted simply because it detects an error or raises an exception. Our tests must also verify the surrounding governance requirements, including logging, quarantine and auditability.

### 2026-10-29 — Yield age reported when it could not be known
- Who noticed: Claude, checking the spread of a new column before opening PR #9 (no test or person caught it)
- Part: 2 (curation)
- What the agent produced: `yield_asat_age_sessions`, how many ASX sessions old the 6 pm yield is
- What was wrong or incomplete: on the first two ASX dates in the history (23–24 Oct 2024) the yield's RBA date was older than the ASX data, so the sessions in between could not be counted; the code reported a small number instead of "unknown"
- How we found it (test, hand check, review): a count of the age values showed unexpected 1s; three were genuine holiday weeks, the first rows were not
- Fix and follow-up (PR link): age left blank when it cannot be counted, before PR #9 was opened
- Lesson / guardrail added: look at the distribution of every new derived column, not just a few rows

### 2026-10-29 — A half-finished trading session entered the metrics
- Who noticed: Claude, running the whole pipeline from an empty folder at 12:20 Sydney, the guardrail adopted after the first Part 1 incident
- Part: 2 (curation)
- What the agent produced: MA20 and Vol20 in the serve table
- What was wrong or incomplete: Yahoo's live bar for a session still trading was treated as a completed session, so an intraday price entered MA20 and Vol20, against our definition ("latest 20 completed trading sessions")
- How we found it (test, hand check, review): the run summary listed 29 Oct as the newest session; its bar was stamped 12:02 pm Sydney
- Fix and follow-up (PR link): bars stamped before 4:15 pm Sydney are labelled `in_progress` and left out of every metric; test added (PR #9)
- Lesson / guardrail added: a Part 1 guardrail caught a Part 2 bug; run end to end at an awkward time of day, not only after the close

### 2026-10-29 — Code rounded where our spec says only the display rounds
- Who noticed: Claude, comparing Maika's METRICS.md v1.1 with the merged code
- Part: 2 (curation)
- What the agent produced: `add_yield_change_5obs` rounded to 0.1 bp inside the calculation (PR #9), a choice the agent made where the spec was silent and listed for us to confirm
- What was wrong or incomplete: v1.1 then decided rounding is for display only and the stored value stays at full precision, so the merged code no longer matched the approved spec
- How we found it (test, hand check, review): review of v1.1 against the code
- Fix and follow-up (PR link): PR #10 stores the value unrounded and adds a test; PR #10 was merged without a recorded approval
- Lesson / guardrail added: when the spec and the code disagree, the code changes, not the spec (our change-control rule)