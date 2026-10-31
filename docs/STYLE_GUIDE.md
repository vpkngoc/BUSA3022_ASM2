# Dashboard Style Guide

## Purpose

This guide sets the minimum design and storytelling standards for management dashboards. It is intended to help analysts communicate a clear decision-relevant story, maintain consistency across future dashboard updates, and avoid visual choices that could mislead non-technical readers.

The primary audience for this project is a financially literate post-trade manager reviewing market conditions at approximately 6:00 pm Sydney time.

## 1. Start with the management question

Every dashboard should make the business question clear before presenting detail.

For this dashboard:

> **How has market activity trended over the past 90 days, and is there anything we should be watching?**

A manager should be able to answer this within approximately **30 seconds** of opening the dashboard.

## 2. Use a clear information hierarchy

Present information in this order:

1. **Takeaway** — one concise statement explaining what happened.
2. **Monitoring signal** — the current Green/Amber/Red status and why it was triggered.
3. **Key indicators** — supporting market, volatility and yield metrics.
4. **Evidence charts** — trends and relationships that explain the headline.
5. **Detailed data** — expandable tables for users who require further investigation.

The most visually prominent element should represent the most decision-relevant information, not simply the largest number.

## 3. Titles should tell the reader what the visual is about

Use short, descriptive chart titles and provide a brief analysis statement where interpretation is required.

Avoid technical or ambiguous labels where a clearer management-facing term is available.

For example:

- **ASX 200 Daily trading volume**
- **Australian 10-year government bond yield**
- **How closely shares and yields move**

Do not state causal conclusions when the evidence only shows association.

## 4. Colour communicates meaning

**Direction and colour have different purposes.**

- Arrows show whether a metric increased or decreased.
- **Green** indicates a favourable or lower-concern outcome.
- **Red** indicates an unfavourable or higher-concern outcome.
- **Amber** indicates elevated conditions requiring attention.
- Where a movement is not clearly favourable or unfavourable, use a neutral or series-specific colour.

Series colours should remain consistent:

- **ASX 200:** blue
- **Moving averages / analytical reference lines:** teal
- **Australian 10-year yield:** distinct orange
- **Correlation / relationship analysis:** purple
- **Pending, provisional or unavailable data:** grey

Green/Amber/Red used in the RAG signal must retain their defined monitoring meaning.

## 5. Make thresholds explicit

A RAG indicator must be based on documented thresholds rather than visual judgement.

For the volume signal:

- **Green:** <30% above the previous 20 completed-session volumes
- **Amber:** 30% to <60% above normal
- **Red:** ≥60% above normal
- **Pending:** latest session volume is not yet final

Thresholds, calculation logic and edge cases must be documented before implementation and reviewed when changed.

## 6. Show freshness and uncertainty

Never make stale, provisional or unavailable data appear current.

The dashboard should clearly distinguish:

- latest completed ASX session;
- current provisional/in-progress session;
- latest available RBA observation;
- last data fetch time.

Missing data should remain visible rather than being silently filled where doing so could change interpretation.

## 7. Keep charts easy to interpret

- Prefer one primary message per visual.
- Avoid unnecessary dual axes.
- Direct-label important series where practical.
- Keep units visible.
- Use rolling averages only when they add meaningful context.
- Highlight unusual observations sparingly.
- Use tables for detailed inspection rather than overcrowding charts.
- Keep visual clutter below the level needed for a 30-second management review.

## 8. Treat correlation carefully

Correlation and fitted relationships provide context, not evidence of causation.

Use wording such as:

> “ASX returns and yield changes were negatively associated over the period.”

Avoid wording such as:

> “Higher yields caused the ASX to fall.”

Where possible, show the correlation value, sample size and time window so the reader can judge the strength and scope of the relationship.

## 9. Analyst handoff and review

A junior analyst maintaining the dashboard should:

- follow this style guide and the documented metric definitions;
- preserve agreed colour and status conventions;
- test any new threshold or metric against historical data;
- verify freshness and point-in-time treatment;
- document material design or calculation changes;
- obtain peer review before merging changes;
- treat AI-generated dashboard code, commentary and visual choices as drafts requiring human validation.

The standard for acceptance is not that a dashboard “looks good”, but that its story, calculations and visual signals are accurate, understandable and reproducible.

## 10. Final 30-second check

Before publishing, ask a reviewer who did not design the dashboard:

1. What happened?
2. Is anything requiring attention?
3. How current is the information?
4. Which visual gave you the answer fastest?
5. Was anything confusing or potentially misleading?

If the reviewer cannot answer the first three questions quickly, revise the dashboard before release.