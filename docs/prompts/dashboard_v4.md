# Dashboard prompt v4

**Supplied by Ngoc on 1 Nov 2026 (00:32 Sydney) as the reference for the next version.** It is quoted verbatim below and was executed as written; it is the prompt for v4. Who drafted the text, and whether an AI tool helped, is for the team to record in `docs/AI_LOG.md` (the row for v4 leaves that field for Ngoc). It builds on Maika's v3 review (`docs/STYLE_GUIDE.md`) and changes one of its rules on purpose: the ASX price change is now green/red as a market-direction convention, not a judgement (section 6A below).

> **Outcome (1 Nov 2026, 11:31):** Ngoc kept the detailed view as the final dashboard and asked for the executive view to be removed. The colour system from this prompt stays in the detailed view; `executive.html` was deleted. The screenshots `docs/img/dashboard_v4_executive*.png` remain as the record of this iteration.

## How Claude applied it (implementation notes, not part of the prompt)

- Two pages from one build: `docs/dashboard/index.html` (detailed, scrollable) and `docs/dashboard/executive.html` (16:9, one screen). Both inline the same `dashboard/common.css` and `dashboard/common.js`, so the data, the range statistics, the chart code, the thresholds and the wording are shared, not copied. `dashboard/indicators.py` and the pipeline are unchanged; a test checks that both pages carry the same script and thresholds.
- Teal shifted from `#13a3a3` to the bluer `#16a6b6` (section 7, "too green"); checked with the dataviz palette validator: against RAG green ΔE 19.4, against the ASX blue 17.5 (floor 15).
- Yield orange `#e3742c` and RAG red `#cc3a5e` kept from v3 (orange vs amber ΔE 15.7, vs red 15.4). Green up vs red down candles are only ΔE 7.7 apart for red-green colour-blind readers, so down candles are hollow and the legend uses the words "Up day" and "Down day" (section 12).
- Volume bars for a pending session are now grey (section 7); before they were the normal-day blue-grey with a "pending" label, which stays.
- Executive view, 1Y period only: when more than four sessions are Red, only the four largest carry a "Red +x%" label, so the labels stay legible. The detailed view labels all of them, as before.
- Table: colour used selectively (section 10 allows neutral): Day % green/red, Signal chips, provisional or in-progress bars grey; everything else neutral, so it never reads as a heatmap.
- Ticker kept in the detailed view only, now on the dark surface instead of the bright blue band; only the signal word carries a RAG colour and the yield value a subtle orange. The executive view shows freshness in the header instead.
- Not changed: data, calculations, thresholds, point-in-time logic, provisional treatment, values, and the conclusions in the analysis text. Wording changed only where the prompt asked: the correlation annotations and the scatter ("association").

## The prompt (verbatim, as supplied)

Kept as plain text so its line breaks and lists read exactly as supplied.

```text
Final Dashboard Refinement — Landscape Executive View + Financial Colour System
Please create the final landscape executive-view version of the existing ASX 200 Market Watch dashboard, while also applying the complete financial colour system specified below.
This is a presentation and visual-governance refinement, not a re-analysis.
The current dashboard already contains the correct analytical components, calculations, business logic and management story. The purpose of this task is to:
reorganise the dashboard into a professional 16:9 landscape executive view that fits on one screen;
apply a consistent financial-market colour system;
make the management story understandable within approximately 30 seconds;
preserve the existing detailed dashboard as the deeper interactive version.

1. Non-negotiable implementation constraints
Do not change:
data sources;
metric definitions;
calculations;
RAG thresholds;
point-in-time logic;
provisional/in-progress treatment;
correlation calculations;
current numerical values;
management conclusions;
dashboard interactions;
underlying analytical meaning.
You may:
reposition components;
condense spacing;
shorten labels where meaning is unchanged;
resize cards and charts;
reorganise panels into rows/columns;
refine colour treatment;
collapse lower-priority detail.
The objective is to create a separate executive presentation layout, not to remove the existing detailed/scrollable dashboard.
Where possible:
retain the detailed dashboard for exploration;
add an executive landscape mode or presentation layout for report/presentation use.

2. Target format
Design the executive view for:
1920 × 1080 pixels
16:9 landscape
Normal browser zoom
No vertical scrolling
All important management information must remain readable at this size.
Do not simply shrink the current tall dashboard until it fits.
Instead, reorganise the components so the page functions as a genuine executive financial dashboard.

3. Management objective
The dashboard must allow a financially literate, non-technical post-trade manager to answer these questions within approximately 30 seconds:
What happened over the last 90 days?
Is anything requiring attention?
How current is the information?
What evidence supports the signal?
How are equity-market conditions interacting with the interest-rate environment?
The reading sequence should therefore be:
Headline → Monitoring signal → Key indicators → Market evidence → Macro context → Relationship evidence
The dashboard should not read like a collection of independent charts.
It should tell one coherent management story.

4. Overall landscape structure
Use four compact horizontal sections.
ROW 1 — Header, takeaway and freshness
Use the full width.
Left / main title
Keep:
ASX 200 & Australian 10-year yield market watch
Subtitle:
Market activity and long-term rates for post-trade review
Centre / main management takeaway
Include one concise 90-day sentence such as:
Over the last 90 days the ASX 200 [movement], while the Australian 10-year yield [movement]. [X] sessions triggered elevated-volume signals; the latest completed signal is Green.
Use the actual current values dynamically.
This should function as the dashboard's executive summary.
Right / compact freshness information
Clearly show:
latest completed ASX signal date;
latest ASX session;
whether that session is final/provisional/in-progress;
latest available RBA observation date;
last successful data fetch.
Do not allow a provisional ASX session or lagged RBA release to appear fully current.
If the existing blue ticker is retained, make it compact and primarily neutral rather than visually dominant.

5. ROW 2 — Main decision area
This row should contain the strongest management information.
Left — Large RAG signal card
Use approximately 25–30% of the page width.
Keep the current structure:
LATEST COMPLETED SIGNAL · [DATE]
GREEN
Normal activity
−3% against its 20-session normal
Also retain:
Latest ASX session [date]: provisional, not yet included.
The RAG card should remain the visually dominant management element.
Use:
Green full card for Green;
Amber full card for Amber;
Red full card for Red;
Grey full card for Pending.
The card answers:
“Is anything requiring attention?”

Right upper — Sessions by Signal
Retain the compact signal strip.
Show:
Green count and percentage;
Amber count and percentage;
Red count and percentage;
Pending count and percentage.
Use:
Green = Green;
Amber = Amber;
Red = Red;
Pending = Grey.
Do not dilute these colours because they represent explicit monitoring states.

Right lower — Four KPI cards in a 2 × 2 grid
Use:
KPI 1 — ASX 200 close
Show:
current close;
provisional badge if relevant;
90-day change.
Colour rule:
main index value = white/light neutral;
provisional badge = grey;
positive ASX price change = green;
negative ASX price change = red.
Only the directional change should receive red/green colour.
Do not colour the entire card.

KPI 2 — Close vs 20-session average
Show:
percentage above/below MA20;
MA20 value.
This is a trend-comparison metric, not a management “good/bad” outcome.
Use:
neutral white/light text; or
teal accent.
Do not automatically make it green because the ASX is above MA20.

KPI 3 — Volatility
Show:
current Vol20;
difference versus 1-year median.
Example:
7.3%
▼3.9 pts · Lower concern vs 1-year median 11.2%
The phrase Lower concern may be green because an explicit management interpretation has been defined.
The main volatility value should remain neutral.
This illustrates:
Arrow = direction
Colour = interpretation

KPI 4 — Australian 10-year yield
Show:
current latest available yield;
RBA as-at date;
latest five-RBA-observation change;
optional 90-day change if space allows.
Do not colour yield increases red or decreases green.
A yield movement is not inherently favourable or unfavourable.
Use:
main value = white/light neutral;
movement = neutral or subtle orange;
arrow = direction only.

6. Overall colour philosophy
The dashboard contains three different colour contexts.
They must remain conceptually separate.

A. Market-price convention
For recognised financial-market price visuals:
Green = price moved up
Red = price moved down
This applies to:
ASX 200 candlesticks;
daily ASX percentage-change values;
other clearly identified equity-price-direction fields.
Here, colour communicates market direction, not whether the outcome is good or bad for the bank.

B. Management monitoring / RAG convention
For explicit monitoring states:
Green = normal / lower concern
Amber = watch / elevated condition
Red = alert / higher concern
Grey = pending / unavailable / provisional
This applies to:
large RAG signal card;
Sessions by Signal;
Signal badges;
abnormal-volume bars;
triggered-session table;
explicit alert text.
Here, colour communicates management interpretation.

C. Neutral analytical-series convention
Metrics without an inherently favourable/unfavourable interpretation should use series-specific colours.
Use:
ASX continuous price series: blue
MA20 / analytical baseline / regression: teal
Australian 10-year government bond yield: true orange
correlation / relationship analysis: purple/lilac
pending / provisional / unavailable: grey
Do not use Green or Red merely because an analytical line rises or falls.

7. ROW 3 — Primary market evidence
Use two approximately equal-width panels.

Left panel — ASX 200 trend
Title:
ASX 200 close
Default to the Baseline view.
Use:
ASX close = blue;
20-session average = teal;
grid/axes = neutral;
above-start/below-start area shading = subdued neutral-blue shades.
Do not use Green/Red area shading in the Baseline view because it competes with the RAG system.
Candlestick toggle
Retain the Baseline / Candles toggle if practical.
For Candles use standard financial-market convention:
Green filled candle = Up day
Red filled/outlined candle = Down day
Teal = 20-session average
Update the legend to:
Green — Up day
Red — Down day
Teal — 20-session average
The teal MA line must remain clearly distinguishable from green candles.

Right panel — ASX 200 Daily trading volume
This chart provides the key evidence behind the RAG signal.
Use:
normal-volume bar = muted blue-grey;
Amber threshold breach = Amber;
Red threshold breach = Red;
Pending = Grey;
20-session normal = cool teal/cyan-teal.
Critical colour correction
The current 20-session normal line appears too green.
Change it to a clearly blue-teal analytical colour.
It must not be mistaken for the Green RAG state.
Therefore:
20-session normal = teal, never RAG Green
Retain important labels such as:
Red +109%
Red +143%
The manager should immediately understand which sessions generated abnormal-volume signals.

8. Triggered sessions
If space allows, place a compact triggered-sessions mini-table beside or below the volume chart.
Show only the five triggered sessions.
Columns:
Session
Signal
vs normal
Use:
Amber chip = Amber;
Red chip = Red;
Amber threshold text = Amber;
Red alert text = Red.
Dates and ordinary text remain neutral.
If the table makes the volume chart too small, prioritise the chart and move the mini-table below it or into an expandable panel.

9. ROW 4 — Macro and relationship context
Use three compact analytical panels.

Panel 1 — Australian 10-year government bond yield
Title:
Australian 10-year government bond yield
Keep the yield as a dedicated macro-series colour.
Yield line colour
Use a true medium orange / copper-orange.
It must not look like:
RAG Red;
RAG Amber;
yellow/gold.
Avoid:
red-orange;
burnt red;
yellow-orange;
golden amber.
The visual meaning should be:
Orange = Australian government-bond yield series
not:
Orange = warning
Awaiting RBA release region
The current pending region should use:
muted grey or blue-grey transparent fill;
subtle grey dashed boundary;
neutral light text.
Do not use reddish/brown shading.
“Awaiting RBA release” means unavailable/pending, not danger.

Panel 2 — Rolling relationship
Title:
How closely shares and yields move
Use:
correlation line = purple/lilac;
area = transparent muted purple;
zero reference line = neutral grey.
Do not use Red simply because correlation is negative.
Negative correlation is not inherently an adverse outcome.
Use non-causal annotation:
Above 0: returns and yield changes tend to move in the same direction
Below 0: returns and yield changes tend to move in opposite directions
Do not use:
“Shares fall when yields rise.”
The chart reports association, not causation.

Panel 3 — Scatter relationship
Title:
Daily ASX return against the yield change
Use:
scatter points = blue;
fitted trend line = teal;
axes/grid = neutral.
Do not use Green for the regression line.
Teal means:
analytical trend/model
not:
favourable result
Retain:
r = [value] · n = [sample size]
Interpretation should use wording such as:
Daily ASX returns and yield changes showed a negative association over the period.
Use:
associated with
rather than causal wording.

10. Detailed table treatment
The existing:
All values in the period (table view)
should remain available in the detailed dashboard, but it should not take space from the one-screen executive layout.
Keep it:
collapsed below the executive view;
expandable;
or accessible through the detailed dashboard mode.
For the table itself, preserve a professional market-table treatment.
Do not turn it into a heatmap.
Use colour selectively.
Session
Neutral.
Bar
Final = neutral
Provisional = Grey
In progress = Grey
Close
Neutral.
Day %
Use normal market convention:
positive / ▲ = Green
negative / ▼ = Red
unchanged = neutral
MA20
Neutral or subtle teal.
Vol20
Neutral.
Volume
Neutral.
vs normal
Prefer neutral because the adjacent Signal column already interprets it.
Signal
Use:
Green badge;
Amber badge;
Red badge;
Pending Grey badge.
10Y values
Neutral or subtle orange accent.
5-observation yield change
Keep arrows, but use neutral or orange text.
Do not treat falling yields as Green or rising yields as Red.
Corr20
Neutral or subtle purple.
Negative correlation should not automatically appear Red.

11. Top information strip
If the information strip is retained, keep it compact and secondary.
Example:
20-session avg ▲1.4% | Volatility 7.3% | 10-yr yield 5.21% | latest 5-RBA-day change ▼6.9 bp | Latest completed signal Green
Use:
ordinary metric text = white/light neutral;
yield values = optional subtle orange;
Green in “Latest completed signal Green” = Green;
provisional/pending = Grey.
Do not colour every number.
The strip should support the dashboard, not compete with the main RAG card.

12. Colour accessibility
Do not rely on colour alone.
Always retain textual labels and/or symbols such as:
Green
Amber
Red
Pending
Up day
Down day
provisional
Lower concern
▲
▼
Ensure sufficient contrast against the dark navy background.
Specifically verify:
Green candles are distinguishable from teal MA20;
Red candles are distinguishable from Red alert bars through context and legend;
teal baselines cannot be mistaken for Green RAG status;
orange yield cannot be mistaken for Amber or Red;
Grey pending treatment remains readable.

13. Final colour hierarchy
The finished dashboard should follow this hierarchy exactly.
Market direction
Green / Red
Used for:
candlesticks;
ASX daily price change.
Monitoring interpretation
Green / Amber / Red / Grey
Used for:
RAG card;
signal strip;
signal badges;
abnormal-volume bars;
triggered sessions.
Market data series
Blue
Used for:
ASX continuous price.
Analytical trend / benchmark
Teal
Used for:
MA20;
20-session normal volume;
regression / fitted trend.
Macroeconomic series
True Orange
Used for:
Australian 10-year government-bond yield.
Relationship analysis
Purple
Used for:
rolling correlation.
Data availability
Grey
Used for:
provisional;
pending;
unavailable;
awaiting RBA release.

14. Typography and visual density
Do not solve the landscape problem by making all text very small.
Instead:
reduce excessive vertical padding;
shorten redundant labels;
reduce unnecessary card height;
use compact KPI cards;
use aligned grids;
reduce duplicated legends;
use direct labels where clearer;
preserve readable axis labels;
maintain clear separation between management and analytical layers.
The page should feel:
dense, controlled and professional
rather than:
compressed or crowded.
Aim for the visual feel of a professional financial-market monitoring interface.

15. What MUST remain visible in the one-screen executive view
At 1920 × 1080, without scrolling, show:
dashboard title;
90-day management takeaway;
freshness / as-at information;
large RAG signal card;
Sessions by Signal;
four KPI cards;
ASX close + MA20 chart;
daily volume + 20-session normal + Amber/Red events;
Australian 10-year yield;
rolling correlation;
scatter relationship if readability permits.
If space becomes constrained, prioritise in this order:
RAG signal;
ASX trend;
volume signal evidence;
key KPI cards;
yield context;
rolling correlation;
scatter relationship;
triggered-session mini-table;
detailed period table.
Do not sacrifice chart readability merely to display every element.

16. Preserve the detailed version
The existing vertically scrollable dashboard remains useful for investigation.
Do not delete it.
The final product should ideally have:
Executive view
16:9 landscape;
one-screen management story;
used in report and presentation.
Detailed view
scrollable;
full charts;
expandable analysis;
row-level table;
used for deeper investigation.
Both views must use the same calculations, thresholds and data.

17. Final quality-control checklist
Before considering the dashboard finished, verify all of the following:
Does the complete executive view fit at 1920 × 1080 without scrolling?
Can a manager identify the current RAG state within a few seconds?
Is the 90-day market story obvious?
Can the user distinguish completed, provisional and pending information?
Are ASX candlestick colours recognisable as Green-up / Red-down?
Is the 20-session volume-normal line clearly teal rather than Green?
Is the yield line clearly Orange rather than Red or Amber?
Is the RBA pending region Grey rather than reddish?
Are correlation and regression visuals analytical rather than judgemental?
Does Green/Amber/Red always have a clear contextual meaning?
Can all important information still be understood without relying on colour alone?
Have all calculations, values, RAG thresholds and analytical conclusions remained unchanged?
Does the final page communicate the management story within approximately 30 seconds?
Does the dashboard resemble a professional financial-market monitoring interface rather than a vertically stacked webpage?
If any answer is no, refine the presentation before finalising.

18. Required final output
Please produce:
the final responsive 16:9 executive dashboard layout;
the refined financial colour system described above;
preservation of the existing detailed/scrollable dashboard;
readable output at 1920 × 1080 and normal browser zoom;
no vertical scrolling in executive mode;
no changes to calculations, values, thresholds or underlying analytical logic;
a short summary of:
which components were repositioned;
which components were condensed;
which colours were changed;
how the final colour system separates market direction, monitoring status and analytical series.
The final result should feel like a professional executive financial-market dashboard: familiar financial conventions where appropriate, strong management signalling where action is required, clear data freshness, disciplined analytical colours and a coherent one-screen story.
```
