# Dashboard v1: every element, for the next critique

Built from `docs/prompts/dashboard_v1.md` (30 Oct 2026; data to Thu 29 Oct 2026). "Range" = follows the 1W / 1M / 3M / 1Y buttons (3M default); "latest" = does not change with the range.

| # | Element | Type | Shows (3M default) | Range or latest | Source |
| --- | --- | --- | --- | --- | --- |
| H | Title + lede | Text | "ASX 200 and Australian 10-year yield market watch" | — | Fixed |
| K | Takeaway box | Text | ASX 200 fell 1.4%; 10-year yield rose 31 bp (RBA data to 21 Oct); volume above normal on 5 of 64 sessions; latest Green | Range | Close, RBA-dated yield, signal |
| S | Running ticker | Ticker (pauses on hover; static if the reader prefers reduced motion) | Close and day change, vs 20-session average, volatility, yield as at 6 pm with 5-obs change, signal, latest session status, last fetch | Latest | Serve table; run log for last fetch |
| F | Range buttons | Control | 1W, 1M, **3M**, 1Y | — | — |
| G | Volume signal | **Gauge** + status chip | +7% vs normal on 28 Oct, Green; zones at +30% and +60% | Latest | Draft M4 |
| D | Sessions by signal | **Donut** + legend with % | 5/64 flagged: Normal 58 (91%), Amber 3 (5%), Red 2 (3%), Pending 1 (2%) | Range | Draft M4 |
| E5 | Tile: ASX 200 close | Stat tile | 8,891.8 (provisional), ▼ 1.4% over the 90 days | Value latest, change range | Close |
| E6 | Tile: close vs 20-session average | Stat tile | ▲ 1.3%, average 8,775.6 | Latest | M1 |
| E7 | Tile: volatility | Stat tile | 7.7%, ▼ 3.5 pts vs 1-year median 11.2% (green: calmer is good) | Latest | M2 |
| E8 | Tile: 10-year yield as at 6 pm | Stat tile | 5.28%, ▼ 3.6 bp over 5 RBA days (green: falling yield is good for shares) | Latest | M3 |
| C1 | ASX 200 close against its start of period | **Baseline chart** (green above / red below the first close) + 20-session average | Start 9,019 | Range | Close, M1 |
| C2 | Daily trading volume | Columns (Amber/Red coloured) + 20-session normal line | 2 Red, 3 Amber; last day "pending" | Range | Volume, draft M4 |
| T1 | Sessions that triggered the signal | Table with coloured chips, beside C2 | 5 rows | Range | Draft M4 |
| C3 | Australian 10-year government bond yield | Line with markers + grey "Awaiting RBA release" band | 4.92%–5.41%, data to 21 Oct | Range | RBA-dated yield |
| C4a | How closely shares and yields move | **Area** around zero (rolling 20-session correlation) | Latest −0.35, range −0.75 to −0.28 | Range | corr20 |
| C4b | Daily ASX return against the yield change | **Scatter** with fitted line | r = −0.44, n = 57 | Range | ASX return, daily yield change |
| A | "Show analysis" on every tile and chart | Expandable text | One or two sentences computed from the data | Range | — |
| T2 | Table view | Table, coloured chips and ▲/▼ | All sessions in the range, 14 columns | Range | All of the above |
| N | Footer | Text | Data sources only; last fetch and build time | — | — |

**Choices made by the agent, to check:** rising yields are coloured red (bad) because they have tended to weigh on shares; the triggered-sessions "vs normal" column is red ▲ (above normal = watch); the gauge runs from −50% to +150%; the donut counts pending sessions separately; 1W shows about five sessions, so its correlation and scatter are thin.
