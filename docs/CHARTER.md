# Project charter

A living document (Week 4): revisited at each phase gate. Last reviewed: 25 Oct 2026.

## 1. Business understanding

| Field | Content |
| --- | --- |
| Business objective | Give post-trade managers a reliable view of how the Australian market has trended over the past 90 calendar days and what to watch, as the first step towards benchmarking the bank against industry data |
| Success criteria (business) | A non-technical manager can explain the dashboard back in 30 seconds; the watch signal fires rarely enough to be acted on; no number is shown without its "as at" date |
| Analytics goal | A scheduled two-source pipeline, three defined metrics, one dashboard view with a Red/Amber/Green signal |
| Success criteria (technical) | Every ingested row is accounted for (rows in = clean + quarantined); all tests pass; metrics match hand-worked values; no backtest uses data before it was published |
| Scope in | ASX 200 daily OHLCV; RBA F2 10-year yield; 3 metrics; 1 dashboard view; proofs of concept for each part |
| Scope out | Forecasting or ML; real-time feeds; a third source; production deployment |

## 2. Situation assessment

| Item | Notes |
| --- | --- |
| Resources | Two team members; Claude as AI coding agent; GitHub (repo, Actions, Pages); Python |
| Constraints | Due 1 Nov 2026; 2,000-word report; 10-minute video; free data sources only |
| Key risks | Yahoo rate limits (429); RBA F2 weekly release lag and revisions; daylight-saving date errors; marker access to a private repo |

## 3. Data understanding

| Source | Access | Known issues (from exploration on 24–25 Oct 2026) |
| --- | --- | --- |
| Yahoo `^AXJO` | HTTPS chart endpoint, no key; needs a browser User-Agent | UTC timestamps (UTC date wrong for every daylight-time session); live partial bar duplicates the latest date with volume 0; volume units are not total market volume (use as relative only); zero volume on 29 Jun 2026 |
| RBA F2 `FCMYGBAG10D` | CSV download, no key | 11 metadata header rows; weekly release; may be revised; no value on 5 Oct 2026 (NSW Labour Day) while the ASX traded |

## 4. Roles (co-leads, equal split)

| Workstream | Owner | Reviewer |
| --- | --- | --- |
| Pipeline (Part 1) | Ngoc | Maika |
| Curation and metrics (Part 2) | Maika | Ngoc |
| Dashboard (Part 3) | Maika | Ngoc |
| Presentation and trade-offs (Part 4) | Ngoc | Maika |
| Code, tests, figures | Claude (AI agent) | Ngoc or Maika, every PR |

## 5. Milestones

| Date | Gate |
| --- | --- |
| Sun 25 Oct | Charter, scaffold, metric requirements committed |
| Mon 26 Oct | PoC 1: pipeline |
| Tue 27 Oct | PoC 2: curation |
| Wed 28 Oct | PoC 3: dashboard; runbook handoff test |
| Thu 29 – Sat 31 Oct | Report and presentation |
| Sun 1 Nov | Submission |
