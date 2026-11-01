# Data dictionary — serve layer

`data/serve/daily_panel.csv` is what the dashboard reads. It is rebuilt after every real pipeline run by `python -m pipeline.align` (or automatically at the end of `python -m pipeline.run`). The metric definitions themselves are the team's, in [`METRICS.md`](METRICS.md); this page describes the columns.

**Grain:** one row per ASX trading session, dated in Sydney (`trade_date_syd`).
**Time axis:** each row describes what a manager could know at the **6:00 pm Sydney review** on that date.
**Missing values:** never filled. A blank cell means "not known" or "not yet enough history".

| Column | Unit | Meaning | Source and rule |
| --- | --- | --- | --- |
| `trade_date_syd` | date | ASX session date in Sydney | Yahoo UTC instant converted to `Australia/Sydney` (Part 1) |
| `review_time_syd` | Sydney local time with offset | 6:00 pm on that date: `+10:00` in winter (AEST), `+11:00` in summer (AEDT) | `pipeline.align.review_instant` |
| `bar_status` | label | `final` (completed daily bar), `provisional` (live bar after the close: close stands, volume not yet known), `in_progress` (run started before the close: shown, but left out of the metrics) | `pipeline.align.mark_provisional` |
| `close_pts` | index points | ASX 200 closing level | Yahoo |
| `volume` | as reported by Yahoo | Session volume. NULL unless the bar is final. Yahoo's index volume is far smaller than total market turnover, so use it for relative comparisons only | Yahoo |
| `ma20_pts` | index points | 20-session moving average of the close | `add_ma20` (METRICS.md) |
| `vol20_ann_pct` | % per year | 20-session annualised realised volatility | `add_vol20` (METRICS.md) |
| `yield_asat_pct` | % per year | Newest RBA 10-year yield **published by 6:00 pm** that day | RBA F2, joined point in time on `available_from_syd` |
| `yield_asat_obs_date` | date | The RBA date that yield belongs to | RBA F2 |
| `yield_asat_age_sessions` | ASX sessions | How many sessions old that yield is (Friday 2 … Thursday 6, because F2 is released weekly). NULL if older than the ASX history | `pipeline.align` |
| `yield_change_5obs_bp` | basis points | 5-observation change of the yield above, calculated on RBA dates before the join; stored at full precision (round to 0.1 bp only when displaying) | `add_yield_change_5obs` (METRICS.md) |
| `yield_same_day_pct` | % per year | The RBA yield dated the same day. **Published days later**: for analysis (e.g. correlation), never shown as if known that evening. NULL when the RBA has no value (e.g. NSW Labour Day) | RBA F2 |
| `dq_flags` | rule IDs | Quality flags carried from the clean tables, prefixed by source, e.g. `asx:DQ03`. `rba:DQ04` marks every session with no same-dated RBA yield: a blank RBA date (NSW Labour Day) or one not published yet | `config/dq_rules.yaml` |

These rules are enforced by `tests/test_serve_contract.py` on the committed data in every pull request: names are `snake_case` with a unit suffix, one row per weekday session, review times carry the right Sydney offset, no session uses a yield published after its review, and the same-day yield is blank, and flagged `rba:DQ04`, exactly where the RBA has no value.

## Dashboard fields (computed when the page is built)

`python -m dashboard.build` reads the serve table above, adds the fields below (`dashboard/indicators.py`) and embeds one year of rows in the page. Nothing here is written back to `data/`. The definition of the signal is the team's M4 in [`METRICS.md`](METRICS.md) v1.2.

| Field | Unit | Meaning | Rule |
| --- | --- | --- | --- |
| `open_pts`, `high_pts`, `low_pts` | index points | Daily open, high and low, for the optional candle view only | `data/curated/asx200_daily.csv` |
| `volume_normal` | as reported by Yahoo | Average of the previous 20 **final, positive** volumes, carried forward to days whose own volume is not final | `add_volume_vs_normal` |
| `volume_vs_normal_pct` | % | Today's final volume against that normal. Blank when the volume is not final | `add_volume_vs_normal` |
| `rag_status` | label | Green below +30%, Amber +30% to below +60%, Red +60% or more; **Pending** while the volume is not final; **Excluded** for a final bar with zero volume (invalid, not a quiet day). No run rule | `add_rag` (`AMBER_AT = 0.30`, `RED_AT = 0.60`) |
| `asx_return_pct` | % | Daily log return of the close (in-progress bars left out) | `add_corr20` |
| `yield_change_1d_bp` | basis points | Change in the same-dated RBA yield from the previous RBA date. Published days later, so for analysis only | `add_corr20` |
| `corr20` | −1 to +1 | Rolling correlation of the two fields above over 20 sessions, with at least 15 pairs; blank on a day without its own pair (RBA value not published yet). Association, not causation | `add_corr20` |

**Latest completed signal** is the newest session whose volume is final; the newest session is often still provisional, so the two dates can differ and both are shown. Period figures (change over the period, signal mix, correlation range, the scatter's r and slope) are computed in the page from these rows for the selected 1W, 1M, 3M (default, 90 calendar days) or 1Y view, by `dashboard/common.js`. `analysis/evidence_pack.py` recomputes the 90-day figures in Python so the report can quote them.
