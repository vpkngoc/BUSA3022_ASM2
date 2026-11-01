# Dashboard Style Guide

## Purpose

This guide defines the minimum storytelling and visual standards for management dashboards. It is designed to help analysts communicate a clear, decision-relevant story, maintain consistency across future updates, and avoid visual choices that could mislead financially literate but non-technical users.

For this project, the primary audience is a post-trade manager reviewing market conditions at approximately 6:00 pm Sydney time.

## 1. Start with the management question

Every dashboard should make the decision question clear before presenting detail.

For this dashboard:

> **How has market activity trended over the past 90 days, and is there anything we should be watching?**

A reviewer should be able to identify the main trend, current monitoring status and data freshness within approximately **30 seconds**.

## 2. Use a clear storytelling hierarchy

Present information in this order:

1. **Takeaway** — what happened.
2. **Monitoring signal** — whether management attention is required.
3. **Key indicators** — market, volatility and yield context.
4. **Evidence charts** — why the headline and signal occurred.
5. **Detailed data** — expandable records for deeper investigation.

The most visually prominent element should represent the most decision-relevant information rather than simply the largest number.

## 3. Use colour according to context

Colour must have an explicit purpose. Do not use colour purely for decoration.

### Market-price convention

Recognised market-price visuals follow familiar financial-market conventions:

- **Green** = price moved up.
- **Red** = price moved down.

This applies to:
- ASX 200 candlesticks;
- daily ASX percentage changes in detailed market tables.

Here, Green and Red describe **market direction**, not whether the movement is favourable for the bank.

### Management monitoring convention

For the RAG monitoring signal:

- **Green** = normal / lower concern.
- **Amber** = watch / elevated condition.
- **Red** = alert / higher concern.
- **Grey** = pending / provisional / unavailable.

This applies to the main signal card, signal badges, Sessions by Signal, abnormal-volume bars and triggered-session reporting.

### Analytical series

Variables without an inherently favourable or unfavourable interpretation use consistent series colours:

- **ASX 200 continuous price:** blue
- **Moving averages / analytical baselines / fitted trends:** teal
- **Australian 10-year government bond yield:** distinct orange
- **Correlation / relationship analysis:** purple
- **Pending / provisional / unavailable information:** grey

Arrows communicate **direction**. Colour communicates either recognised market direction or an explicitly defined management interpretation.

## 4. Make signal thresholds explicit

The RAG indicator must be based on documented rules rather than visual judgement.

For the volume signal:

- **Green:** <30% above the previous 20 completed-session normal
- **Amber:** 30% to <60% above normal
- **Red:** ≥60% above normal
- **Pending:** latest session volume is not final

Thresholds, calculation rules and edge cases must be documented and tested before implementation changes are accepted.

## 5. Show freshness and uncertainty

Never make stale, provisional or unavailable data appear current.

Clearly distinguish:

- latest completed ASX session;
- provisional/in-progress ASX session;
- latest available RBA observation;
- last successful data fetch.

Pending or unavailable periods should use neutral grey treatment. Missing data must not be silently hidden or filled where doing so could change interpretation.

## 6. Keep charts easy to interpret

- One primary message per visual.
- Use clear management-facing titles and visible units.
- Avoid unnecessary dual axes.
- Keep series colours consistent across the dashboard.
- Highlight only meaningful exceptions.
- Use tables for detail rather than overcrowding charts.
- Preserve familiar financial conventions for candlesticks and price changes.
- Use analytical colours rather than RAG colours for moving averages, yield series and relationships.

## 7. Treat relationships carefully

Correlation and fitted relationships provide context, not evidence of causation.

Prefer:

> “ASX returns and yield changes were negatively associated over the period.”

Avoid:

> “Higher yields caused the ASX to fall.”

Where practical, show the correlation value, sample size and time window so the reader can judge the strength and scope of the relationship.

## 8. Analyst handoff and review

A junior analyst maintaining the dashboard should:

- follow this guide and the documented metric definitions;
- preserve established colour and status conventions;
- test new thresholds or metrics before release;
- verify point-in-time treatment and freshness;
- document material calculation or visual changes;
- obtain peer review before merging changes;
- treat AI-generated code, commentary and visual recommendations as drafts requiring human validation.

The acceptance standard is not that the dashboard simply “looks good”. Its story, calculations, visual signals and data-status treatment must be accurate, understandable and reproducible.

## 9. Final 30-second review

Before release, ask a reviewer who did not design the dashboard:

1. What happened?
2. Is anything requiring attention?
3. How current is the information?
4. Which visual gave you the answer fastest?
5. Was anything confusing or potentially misleading?

If the reviewer cannot answer the first three questions quickly, revise the dashboard before publication.