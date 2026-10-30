# Dashboard v0: every element, for critique

Built by the AI agent from `docs/prompts/dashboard_v0.md` (30 Oct 2026; data to Thu 29 Oct 2026). Values are as built and will shift nightly. "Source" names the column or calculation, so each element can be traced, kept, changed or cut.

## Text

| # | Element | Shows (v0) | Source / rule | Questions for the critique |
| --- | --- | --- | --- | --- |
| E1 | Headline | "ASX 200 down 1.4% in 90 days while the 10-year yield rose 31 bp" | First vs last close in the window; first vs last **RBA-dated** yield (3 Aug to 21 Oct) | Is this the Big Idea a manager needs? The as-at yield rose 34 bp over the same window: two yield numbers on one page |
| E2 | Dek | "Shares and long-term rates kept moving in opposite directions… volume ran well above normal on 5 of 64 sessions; the latest final session is Green." | Correlation stayed negative all window; RAG counts | "Kept moving in opposite directions" is a strong reading of a −0.28 to −0.75 correlation |
| E3 | As-at strip | Window 3 Aug – 29 Oct (64 sessions) · ASX close 29 Oct (provisional) · RBA yield as at 21 Oct (6 sessions old) · build time | `bar_status`, `yield_asat_obs_date`, `yield_asat_age_sessions` | Too technical? "provisional" and "sessions old" need plain words? |

## Signal and tiles

| # | Element | Shows (v0) | Source / rule | Questions for the critique |
| --- | --- | --- | --- | --- |
| E4 | RAG card: volume vs normal | **Green**, Wed 28 Oct +7% vs normal; fired 5 of 64 sessions (3 Amber, 2 Red); rule line; action text | **Draft M4**: volume ÷ average of previous 20 final, positive volumes − 1. Amber ≥ +30%; Red ≥ +60% or Amber 3 in a row; Pending if not final | Is volume the right signal for post-trade? Are the thresholds right? The **action text was written by the agent** (Amber: check for a known cause; Red: raise at the morning stand-up): the team must own it. Status is for 28 Oct, not 29 Oct |
| E5 | Tile: ASX 200 close | 8,891.8 · −1.4% over 90 days | `close_pts` (29 Oct, provisional) | Should it say "provisional"? |
| E6 | Tile: against 20-session average | +1.3% · average 8,775.6 pts | M1 `ma20_pts` | Is "% above trend" meaningful to managers? |
| E7 | Tile: 20-session volatility | 7.7% a year · 1-year median 11.2% | M2 `vol20_ann_pct`; median of the last 365 days | "Calmer than usual" is the message: say it in words? |
| E8 | Tile: 10-year yield (as at 6 pm) | 5.28% · −3.6 bp over 5 RBA days · dated Wed 21 Oct | M3 `yield_asat_pct`, `yield_change_5obs_bp` | Headline says +31 bp, tile says −3.6 bp: different windows, likely confusing |

## Charts (one shared 90-day date axis, weekends removed)

| # | Element | Shows (v0) | Source / rule | Questions for the critique |
| --- | --- | --- | --- | --- |
| C1 | Price | Close (blue) and 20-session average (grey), end labels; title "The index closed above its 20-session average (+1.3%)" | `close_pts`, `ma20_pts` | Does the title tell the 90-day story (fell from 9,270 in Aug to 8,620 in early Oct, then recovered)? |
| C2 | Volume | Columns grey; Amber and Red days in status colours; 20-session normal line; last day "pending"; title "Volume spiked on 5 sessions; 2 reached Red" | `volume`, `volume_normal`, `rag_status` | Label the two Red days with their likely cause (31 Aug month end, 18 Sep quarterly expiry; **unverified**)? |
| C3 | Yield | 10-year yield by RBA date (orange), gap on Labour Day, shaded "awaiting RBA release" band after 21 Oct; title "The 10-year yield rose 31 bp to 5.28% (RBA data to 21 Oct)" | `yield_same_day_pct` | Should the as-at (step) line be shown too, to match the tile? |
| C4 | Overlay: correlation | Rolling 20-session correlation, −1 to +1 scale, zero line, plain labels; title "Shares usually fell when yields rose: latest correlation −0.35 (range −0.75 to −0.28)" | New: daily ASX log return (%) vs same-day yield change (bp), 20 sessions, at least 15 pairs | Will a non-technical manager read a correlation line? Show divergence instead (days when both rose or both fell)? |

## Tables and notes

| # | Element | Shows (v0) | Questions for the critique |
| --- | --- | --- | --- |
| T1 | Triggered sessions | 5 rows: date, Amber/Red, % vs normal | Add a "what happened" column? |
| T2 | Table view (collapsed) | 64 rows × 13 columns, newest first | Needed for accessibility; is it too wide on a phone? |
| N1–N5 | Notes | Sources; time axis; volume caveat; M4 is a draft; where definitions live | Too long? Should some move next to the charts they explain? |

## Data used

- From `data/serve/daily_panel.csv`: `trade_date_syd`, `bar_status`, `close_pts`, `volume`, `ma20_pts`, `vol20_ann_pct`, `yield_asat_pct`, `yield_asat_obs_date`, `yield_asat_age_sessions`, `yield_change_5obs_bp`, `yield_same_day_pct`, `review_time_syd`.
- From `data/curated/au10y_daily.csv`: `value_pct`, for daily yield changes.
- Calculated in `dashboard/indicators.py` (draft, tested in `tests/test_dashboard.py`): `volume_normal`, `volume_vs_normal_pct`, `rag_status`, `asx_return_pct`, `yield_change_1d_bp`, `corr20`, the 90-day window and the summary figures.

## Not shown in v0 (choices to question)

The as-at yield as a line; quality flags (`dq_flags`); a 1-year range band for volatility; MA20 crossover markers; event labels; divergence shading; any comparison with the bank's own activity (the brief's benchmarking aim).

## Design

One page, summary before detail. IBM Plex Sans (text) and IBM Plex Mono (labels). Colour: ASX blue, yield orange; status colours only for the RAG, always with a word. No dual axes; light and dark themes; works at 400 px; hover tooltips; zoom disabled.
