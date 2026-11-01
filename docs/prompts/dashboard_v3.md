# Dashboard prompt v3

**Written by Claude on 31 Oct 2026 from Maika's fresh-eyes review of v2.2**, quoted verbatim below as Ngoc passed it on. Maika did not write or see the earlier prompts, so this is the independent review the plan asked for. Her principles are also in `docs/STYLE_GUIDE.md` (commit `4a15c88`). Ngoc and Maika confirm or edit this prompt before the v3 PR is merged.

## The human input (verbatim, Maika)

> Colour meaning should stay disciplined
> Color usage rule: Green indicates a favourable or lower-concern outcome; Red indicates an unfavourable or higher-concern outcome, regardless of whether the metric moves up or down. Arrow direction shows movement only. Where a movement is not inherently favourable or unfavourable, use a neutral colour instead.
>
> | KPI | Arrow | Colour | Why |
> | --- | --- | --- | --- |
> | ASX 200 close | ▼ 1.4% | Neutral | A falling index is not automatically "bad" for a post-trade manager |
> | Close vs MA20 | ▲ 1.3% | Neutral | Above MA20 indicates trend, not necessarily a favourable outcome |
> | Volatility | ▼ 3.5 pts | Green if you define lower volatility as lower monitoring concern | Down can be favourable |
> | 10-year yield | ▼ 3.6 bp | Neutral | Falling yield is not universally good |
> | Volume RAG | Green / Amber / Red | Semantic colour | Thresholds explicitly define monitoring severity |
>
> So your principle becomes: Arrow = direction; Colour = interpretation. For example: ▼ 3.5 pts in green = volatility fell, which is lower concern; ▲ 70% vs normal volume in red = volume rose, but it crossed the alert threshold; ▼ 3.6 bp yield in neutral = direction is known, but favourability is not. I would also add explicit words where colour could otherwise be ambiguous: ▼ 3.5 pts — Lower concern, or ▲ 70% — Red alert. That makes the convention very easy for a manager to learn.
>
> Adjustment for Chart "ASX 200 Daily trading volume": the bars are already doing exactly what we want: normal sessions are neutral blue-grey, Amber sessions are amber, and Red sessions are red. Keep all of that. The one thing I would change is the "20-session normal" line. At the moment it reads visually as green, which competes with Green as a RAG state. Change that line to a distinct teal/cyan instead. The wording in the expanded analysis — "Latest final session +7% (Green)" — can stay green because it is explicitly referring to the RAG status.
>
> 2. The top summary and the metric cards mix different comparison windows. For example: headline says yield rose 31 bp over the broader 90-day story; KPI card says ▼ 3.6 bp over 5 RBA days · 21 Oct. Both can be valid, but together they feel like two different stories. What to do: keep both only if you label them more clearly: 90-day change: +31 bp; Latest 5-RBA-day change: −3.6 bp. Otherwise a reader may think the dashboard is inconsistent.
>
> 3. "Latest signal" vs "latest session" may confuse readers. Right now I can see: Volume signal Green (28 Oct); Latest session Thu, 29 Oct · provisional. This makes sense technically, but a manager may pause and think: "So is the latest day Green or not?" Better wording: Latest completed signal: Green (Wed, 28 Oct); Latest ASX session: Thu, 29 Oct — provisional, not yet included in signal assessment.
>
> 4. Correlation panel, "How closely shares and yields move": change analysis to: Daily ASX returns and yield changes remained negatively correlated, although the strength varied over the period. Latest: −0.35; range: −0.75 to −0.28.
>
> 5. Correlation panel, "Daily ASX return against the yield change": Across 57 matched sessions, daily ASX returns and yield changes were moderately negatively correlated (r = −0.44). The fitted relationship was approximately −0.059 percentage points of ASX return per +1 bp yield change, describing association rather than causation.

## Prompt v3

> Revise dashboard v2.2, keeping its layout, data and rules, with these changes.
>
> **Colour discipline (arrow = direction, colour = interpretation).** Arrows always show direction. Colour shows management interpretation only: green for favourable or lower concern, red for unfavourable or higher concern, amber for elevated, and a neutral colour where the movement has no clear favourable reading. Apply it everywhere a change is shown (tiles, ticker, tables):
> - ASX 200 change, close vs 20-session average, daily return, 10-year yield changes: **neutral**.
> - Volatility: **green with the words "Lower concern"** when it is below its 1-year median, **red with "Higher concern"** when above.
> - Volume vs normal: the RAG colour of that session, with the words ("Amber", "Red alert").
> - The price chart's shading above and below the start of the period, and the candles, become neutral (blue and blue-grey), because a falling index is not in itself bad.
>
> **Reference lines in teal.** The 20-session average and the 20-session normal become a teal that cannot be mistaken for RAG green; shift the ASX blue slightly so the two lines stay distinguishable. Grey stays reserved for pending or unavailable data.
>
> **Label every comparison window.** Wherever a change is shown, say its window: "90-day change" (or the selected period) in the highlights and tiles, "Latest 5-RBA-day change" on the yield tile, "today" in the ticker.
>
> **Signal vs session.** Call the signal "Latest completed signal" with its weekday and date, and the newest bar "Latest ASX session … provisional, not yet included in signal assessment" in the ticker, the signal card and the highlights.
>
> **Correlation wording.** Use Maika's wording for both correlation analyses, computed from the data for the selected period: the rolling panel says the link "remained negatively correlated, although the strength varied" when it stayed below zero, with latest and range; the scatter says how many matched sessions, the strength in words (weak below 0.3, moderate 0.3–0.5, strong above 0.5), r, the fitted slope in percentage points per +1 bp, and "association rather than causation".
