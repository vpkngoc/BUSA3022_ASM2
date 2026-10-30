# Dashboard prompt v1

**Written by Claude on 30 Oct 2026 from Ngoc's critique of v0.** The critique is quoted below exactly as he wrote it in the Part 3 critique worksheet, plus his message of 30 Oct, 19:08 Sydney. The prompt turns that critique into instructions; Ngoc confirms or edits it before PR #13 is merged. Built as dashboard v1 (PR #13, second commit).

## The human input (verbatim)

| Element | Ngoc's critique of v0 |
| --- | --- |
| E1 Headline | "Keep the headline as general title and bring the headline as separate takeaway box under the title but before the cards and stripes." |
| E3 As-at strip | "Make this as a running stripe. The "build time" reword as "last fetch"" |
| E4 RAG card | "apply color to the text to imply indicator is saying good or bad, green for increasing and good with ▲, red for decreasing or bad ▼; better highlight visualization for the signal; the session data display as 5/64 anf 3 amber 2 red displayed as percentage pie or donut chart, no text-heavy" |
| E5–E8 Tiles | "General title of the chart, describing instead of stating insights, add in an option to click to see the summary of analysis" (written on each of the four rows) |
| C1 Price | "larger line, baseline chart with shaded area for the close line" |
| C2 Volume | "larger line" |
| C3 Yield | "i like the marking of awaiting RBA release, this is the gray area worth noting" |
| T1 Triggered sessions | "bring up close to the volume chart, can do side by side, imply color for the signal in this table as well" |
| T2 Table view | "this one is good, imply color for data where needed" |
| N Notes | "Only state the data sources" |

Message, 30 Oct 19:08: "fix the visuals and layout first … build the dashboard in dark theme, add in filter option like mode view button to see the trend in 1 week, 1 month, 1 year but the default is still the one stated by the brief 90 days … also consider using other chart type rather than just line and bar."

E2 (dek) and C4 (correlation) had no comment and are kept.

## Prompt v1

> Rebuild the market-watch dashboard (v0) for the post-trade managers' 6 pm review, keeping the data, metrics and rules of v0, with these changes.
>
> **Theme and layout.** A dark theme throughout. Order from the top: a general, descriptive page title; directly under it a **takeaway box** with the computed insight (the v0 headline and dek); then a **running ticker strip** with the latest figures and "last fetch" (the time the pipeline last fetched the data, not the build time); then the range buttons; then the signal, the tiles and the charts.
>
> **Range buttons.** 1W, 1M, 3M and 1Y. **3M (the brief's 90 days) is the default.** One row of buttons above everything they control. The takeaway, the deltas, the signal counts, the charts and the tables all follow the selected range. The latest values (close, 20-session average, volatility, yield as at 6 pm, today's signal) do not change with the range.
>
> **Signal, not text.** Show today's volume-vs-normal as a **gauge** with Green, Amber and Red zones at +30% and +60%. Show the mix of sessions in the range (normal, Amber, Red, pending) as a **donut** with "flagged / total" in the middle. Keep the words short.
>
> **Good/bad colour on numbers.** Every change carries ▲ or ▼ and is green when it is good for the reader, red when it is bad. Index up or above its average is good. Volatility up is bad. Yield up is shown red, because rising yields have tended to weigh on shares (the overlay shows this).
>
> **Titles and analysis.** Tiles and charts get general, descriptive titles. Each has a "Show analysis" control that reveals a one-to-two sentence summary computed from the data for the selected range.
>
> **Charts** (one shared date axis, weekends removed):
> 1. Price as a **baseline chart**: the close as a thicker line, shaded green above and red below the close at the start of the range; the 20-session average as a second, thinner line.
> 2. Volume columns with Amber and Red days in status colours and a thicker 20-session normal line, with the **triggered-sessions table beside it**, its signal column coloured.
> 3. The 10-year yield by RBA date, keeping the **grey "awaiting RBA release" band**.
> 4. The rates-and-shares relationship in two views side by side: the rolling 20-session correlation as an **area** above or below zero, and a **scatter** of each day's ASX return against that day's yield change, with a fitted line and its correlation.
>
> **Tables.** The full table view stays, with coloured signal chips and ▲/▼ colour on changes. **Notes list only the data sources.**
>
> **Unchanged.** No dual axes; status colours only for the signal and good/bad changes, always with a word or arrow; never show pending volume as zero or imply a yield was known the evening it is dated; works at phone width; rebuilt nightly; tests pass.
