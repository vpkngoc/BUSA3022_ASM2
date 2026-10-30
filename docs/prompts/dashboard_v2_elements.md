# Dashboard v2: every element, for the next critique

Built from `docs/prompts/dashboard_v2.md` (30 Oct 2026; data to Thu 29 Oct 2026). "Period" = follows the View period buttons (3M default); "latest" = does not change with the period.

| # | Element | Type | Shows (3M default) | Period or latest |
| --- | --- | --- | --- | --- |
| H | Title + lede | Text | "ASX 200 and Australian 10-year yield market watch" | — |
| K | Takeaway box | Text | ASX 200 fell 1.4%; yield rose 31 bp (RBA data to 21 Oct); 5 of 64 sessions flagged; latest Green | Period |
| S | Ticker | Blue running strip | Close and day change, vs average, volatility, yield as at 6 pm, signal, latest session, last fetch | Latest |
| F | View period | Buttons | 1W, 1M, **3M**, 1Y | — |
| G | Volume signal card | Status-colour panel + action + 3-rung threshold ladder | **GREEN**, "Normal activity", +7% on 28 Oct; "No action"; ladder marks Green | Latest |
| D | Sessions by signal | Session strip (one cell per session) + counts | 58 Green (91%), 3 Amber (5%), 2 Red (3%), 1 Pending (2%) | Period |
| E5–E8 | Tiles | Stat tiles with ▲/▼ good/bad colour | Close 8,891.8 ▼1.4%; vs average ▲1.3%; volatility 7.7% ▼3.5 pts vs median; yield 5.28% ▼3.6 bp | Value latest, change period |
| C1 | ASX 200 close | Baseline chart (default) or candlesticks (option); aqua 20-session average | Start 9,019 | Period |
| C2 | Daily trading volume | Columns, Amber/Red coloured, Red days labelled; aqua normal line | Red +109% (31 Aug), Red +143% (18 Sep) | Period |
| T1 | Sessions that triggered the signal | Table with coloured chips, beside C2 | 5 rows | Period |
| C3 | Australian 10-year government bond yield | Line + orange "Awaiting RBA release" band | 4.92%–5.41%, data to 21 Oct | Period |
| C4a | How closely shares and yields move | Violet area around zero | Latest −0.35 (−0.75 to −0.28) | Period |
| C4b | Daily ASX return against the yield change | Scatter, aqua fitted line | r = −0.44, n = 57 | Period |
| A | Show analysis | One dense line per tile and chart | e.g. "Volume spiked on 5 sessions; 2 reached Red, the largest +143% on 18 Sep" | Period |
| T2 | Table view | Table, chips and ▲/▼ | All sessions in the period | Period |
| N | Footer | Text | Data sources; last fetch and build time | — |

**Candles, critically.** Over the last 90 days Yahoo's open for this index equalled the previous close on every session (92% over two years), so a candle body only repeats the day's change; the wick adds the intraday range (median 0.8% of the close). Useful at 1W/1M, cluttered at 3M/1Y and less familiar to non-technical readers, so it is an option, not the default.

**Choices to check:** rising yields still red; the triggered-sessions "vs normal" column red ▲; the signal card shows the latest *final* session (28 Oct), while the ticker's latest session is 29 Oct (provisional).
