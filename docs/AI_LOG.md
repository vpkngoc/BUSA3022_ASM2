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
| --- | --- | --- | --- |
| v0 | Agent-written baseline, at the team's request: verbatim in `docs/prompts/dashboard_v0.md` | Ngoc's critique (Part 3 worksheet, 30 Oct): the insight was the page title instead of a separate takeaway; the as-at line was static and said "build time" instead of "last fetch"; the signal was text-heavy, with no good/bad colour and no visual of the session mix; tile and chart titles stated conclusions instead of describing, with no way to open the analysis; lines too thin; price was a plain line; the triggered-sessions table sat far from the volume chart and was uncoloured; notes were too long; light theme; no range choice | `docs/img/dashboard_v0.png` |
| v1 | Written by Claude from Ngoc's critique, which is quoted verbatim in `docs/prompts/dashboard_v1.md` with his 30 Oct 19:08 message; Ngoc to confirm | Ngoc's critique (30 Oct 20:36, verbatim in `docs/prompts/dashboard_v2.md`): the ticker blended into the page; the blue theme needed another shade; the range buttons had no title; the hidden analysis was wordier than v0's punchy insight lines; the signal card did not lead with the RAG colour and its meaning; the donut took too much attention for a side visual; grey lines blended into the dark theme; candles not considered; the grey "awaiting RBA release" band | `docs/img/dashboard_v1.png` |
| v2 | Written by Claude from Ngoc's critique of v1 and his M4 in `docs/METRICS.md` v1.2: `docs/prompts/dashboard_v2.md`; Ngoc to confirm | (to be filled after the critique of v2) | `docs/img/dashboard_v2.png`, `docs/img/dashboard_v2_candles_1m.png` |
| v2 + edits | No prompt: Ngoc edited the wording directly (commits `908a3b1`, `e35f7d7`): "Market Move Monitor" eyebrow, "Highlights" instead of "Takeaway", shorter chart subtitles, shorter tile labels, the period hint removed | A human edit, not an agent output. His merge of the branch first restored the v1 layout; the v2 layout was put back with his wording, and a test now fails if the layout regresses | `docs/img/dashboard_v2_1.png` |
| v2.2 | "get rid of this part" (Ngoc, 30 Oct 21:53, with a screenshot of the signal card's action text, threshold ladder and rule line) | Maika's fresh-eyes review of v2.2 (31 Oct, verbatim in `docs/prompts/dashboard_v3.md`): colour mixed direction with judgement (a falling index and a falling yield shown green or red); the teal-green normal line competed with RAG green; the highlights (+31 bp over 90 days) and the yield tile (−3.6 bp over 5 RBA days) used different windows without saying so; "Volume signal 28 Oct" next to "Latest session 29 Oct" left a manager unsure whether the latest day was Green; the correlation wording needed to describe association, strength and sample | `docs/img/dashboard_v2_2.png` |
| v3 | Written by Claude from Maika's review: `docs/prompts/dashboard_v3.md`; Ngoc and Maika to confirm | From prompt v4 (supplied by Ngoc, 1 Nov, verbatim in `docs/prompts/dashboard_v4.md`): a tall scrolling page, not a one-screen management story for the report and presentation; the three colour contexts were mixed (candles and the daily ASX change neutral instead of the familiar green-up/red-down market convention); the 20-session normal still read as green; the yield line was red-orange and the "awaiting RBA release" band orange, so both looked like warnings; the correlation note "shares fall when yields rise" was causal; the scatter said "correlated" where "association" was meant; the bright blue ticker competed with the RAG card | `docs/img/dashboard_v3.png` |
| v4 | Supplied by Ngoc as written: `docs/prompts/dashboard_v4.md` (drafted by: Ngoc to record, including any AI tool used) | (to be filled after the review of v4) | `docs/img/dashboard_v4_executive.png`, `docs/img/dashboard_v4_executive_candles_1m.png`, `docs/img/dashboard_v4_detail.png` |

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

### 2026-10-31 — Correlation reported for days whose yield was not yet published
- Who noticed: Claude, while applying Maika's correlation wording to the data fetched on 31 Oct (entry drafted by Claude; the team verifies and rewords it before merging)
- Part: 3 (dashboard)
- What the agent produced: the rolling 20-session correlation in the dashboard (PR #13)
- What was wrong or incomplete: it also gave a value on sessions with no published RBA yield yet. Those windows were simply the previous window minus its oldest pair, so after Friday's release the "latest" value drifted from −0.26 to +0.04 and Maika's sentence "remained negatively correlated" would have been reported as false
- How we found it (test, hand check, review): the new figures contradicted the reviewer's wording, so the last eight values were checked by hand against the daily pairs
- Fix and follow-up (PR link): the correlation is now blank on a day without its own pair, and a test covers it (v3 PR)
- Lesson / guardrail added: a rolling statistic must end on a day that has data; a reviewer's wording written on yesterday's data is a useful check on today's numbers

