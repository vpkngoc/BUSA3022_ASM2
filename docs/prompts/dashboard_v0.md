# Dashboard prompt v0 (baseline written by the AI agent)

**Author: Claude (AI agent), 30 Oct 2026, at the team's request.** This is the agent's own reading of the brief, used to build dashboard v0 (`dashboard/`, PR #13). It is the starting point for reverse prompt engineering: the team critiques v0 and its element list (`docs/prompts/dashboard_v0_elements.md`), then writes v1 of the prompt in their own words. Later versions are logged in the *Prompt iterations* table in `docs/AI_LOG.md`.

---

> Build an evening market-watch dashboard for Really Big Bank's post-trade managers: financially literate, not technical, reading it at the 6:00 pm Sydney review. It must answer the brief's question, "How has market activity trended over the past 90 days, and is there anything we should be watching?", within 30 seconds.
>
> **Data.** Use only `data/serve/daily_panel.csv` (one row per ASX session in Sydney time, Part 2) and `data/curated/au10y_daily.csv` (for daily yield changes). Window: the last 90 calendar days ending at the newest session.
>
> **Top of the page.**
> 1. A takeaway headline computed from the data (direction and size of the ASX 200 move and the 10-year yield move over the window), with a one-sentence dek.
> 2. An "as at" strip: the window, whether the newest ASX close is final or provisional, the date and age in sessions of the RBA yield as at 6 pm, and the build time.
> 3. One RAG signal card: daily volume against its normal. Draft metric M4 (not yet in METRICS.md, label it as a draft): normal = average of the previous 20 final, positive volumes; Amber at least +30%; Red at least +60%, or Amber three sessions in a row; Pending when the volume is not final. Show today's status in words and colour, the percentage, how many times it fired in the window (Amber and Red), and what a manager should do when it fires.
> 4. Four stat tiles: ASX 200 close and its 90-day change; close against its 20-session average; 20-session volatility against its 1-year median; the 10-year yield as at 6 pm with its 5-observation change and its RBA date.
>
> **Four charts on one shared 90-day date axis** (weekends removed), each with a takeaway title and a one-line subtitle naming the measure and units:
> 1. ASX 200 close with its 20-session moving average, direct end labels.
> 2. Daily volume columns, normal days neutral, Amber and Red days in status colours, the 20-session normal as a line; a pending day is marked "pending", never drawn as zero.
> 3. The RBA 10-year yield on its own RBA dates (a gap where the RBA has no value), with a shaded "awaiting RBA release" band from the last published date to the newest session.
> 4. The rolling 20-session correlation between the daily ASX log return and the same-day change in the yield, on a fixed −1 to +1 scale, with the zero line and plain-language labels for −1 and +1.
>
> **Below the charts:** a table of the sessions that triggered the signal; a collapsible table view of every value in the window; notes on sources, the time axis, volume caveats and the draft status of M4.
>
> **Rules.** No dual axes (separate aligned panels instead). Colour carries identity only: ASX blue, yield orange, and status colours only for the RAG, always with a word next to them. Label lines directly; legends above charts; hover tooltips with values. Never imply the yield was known on the evening it is dated; never show a missing volume as zero. Light and dark themes; works at phone width.
>
> **Build.** Python reads the data and writes one self-contained HTML page (Plotly.js from a CDN) to `docs/dashboard/index.html`, ready for GitHub Pages; the nightly ingest workflow rebuilds it after each real run. Test the signal logic (thresholds, the three-in-a-row rule, pending days, the 90-day window) and that the page builds from the committed data.
