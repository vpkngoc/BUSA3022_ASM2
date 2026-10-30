# Dashboard prompt v2

**Written by Claude on 30 Oct 2026 from Ngoc's critique of v1** (quoted verbatim below) and from M4 as Ngoc defined it in `docs/METRICS.md` v1.2 (commit `aa12944`, 30 Oct 19:20). Ngoc confirms or edits this prompt before PR #13 is merged. Built as dashboard v2 (PR #13).

## The human input (verbatim)

Message, 30 Oct 20:36: "the running ticket add blue background, reconsider to choose another shade of blue for the theme, add title for the view mode "View Period", make the insights when click on analysis dense as the previous version we just hiding it, the volume signal card design the visuals again the biggest highlight is the color of the RAG, what it tells, change the donut to fill up ladder or something this visual is just the side one, avoid using grey line in the chart kinda mix with the theme and hard to see, consider using candles chart be critical whether to use or not, fix the gray shade area of the waiting RBA release to different color not gray"

## What M4 v1.2 changes in the code

- **Red is +60% or more only.** v0 and v1 also turned three Amber sessions in a row into Red; M4 v1.2 does not include that rule, so it is removed (the code follows the spec).
- **A zero-volume session is invalid and excluded**, not "pending": it gets its own status, *Excluded*, and stays out of every baseline.
- **The Amber and Red actions** are M4's own wording, shown on the signal card.
- **Red days are labelled on the chart** ("Label the event on the chart").

## Prompt v2

> Revise dashboard v1, keeping its data, ranges and rules, with these changes.
>
> **Theme.** Move the dark theme to a deep navy with a different, clearer blue as the accent. Give the running ticker a solid blue background with white text.
>
> **View period.** Label the range buttons "View period". 3M (90 days) stays the default.
>
> **Analysis text.** Under each "Show analysis", give one dense line that states the insight with its numbers, in the style of v0's chart titles (for example "Volume spiked on 5 sessions; 2 reached Red, the largest +143% on 18 Sep"). Keep it hidden until clicked.
>
> **Volume signal card.** Make the RAG colour the dominant element: the card's top half is filled with the status colour and shows the status word, what it means, today's % against normal and the date. Below it, M4's action for that status, and a three-rung **threshold ladder** (Green below +30%, Amber +30% to +60%, Red +60% or more) with today's value marked on its rung. Use M4 v1.2 exactly: Red at +60% or more; zero-volume days are Excluded; the newest day is Pending until final.
>
> **Session mix.** Replace the donut with a secondary **session strip**: one small cell per session in the range, in date order, coloured by its signal, with the counts and percentages beside it.
>
> **No grey lines.** Draw lines in distinct series colours that stand out on navy: the 20-session average and the 20-session normal in aqua (both are "normal" levels), the correlation line in violet, the fitted line in aqua. Keep the ASX in blue and the yield in orange.
>
> **Candles.** Evaluate candlesticks critically. For this index Yahoo's open always equals the previous close in the window, so a candle body only repeats the day's change; the wick adds the intraday range. Offer candles as an option on the price chart (Baseline | Candles), not the default, and say what the candle shows.
>
> **Awaiting RBA release.** Shade the not-yet-published period in a light wash of the yield's own orange, not grey, with its label.
>
> **Red days.** Label each Red day on the volume chart with its % against normal.
