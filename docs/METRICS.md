# Metric requirements (plain language)

> **To be written by the team, in your own words, and committed before any transform code.**  
> The commit history is the evidence that requirements came before the agent wrote code (AI Agent lens, Part 2).  
> Claude must not fill this file in. After we commit it, Claude will implement exactly what it says and flag anything ambiguous.

For each metric, complete every field.

## M1 — 20-session moving average

- **Definition:**  
  The 20-session moving average shows the average closing level of the S&P/ASX 200 across the most recent 20 completed trading sessions. We use it to smooth out daily price movements and make the underlying market direction easier to see.

- **Calculation (formula, window N, units):**  
  For each trading day, calculate the average of the current ASX 200 closing price and the previous 19 valid closing prices.  
  
  `MA20(t) = (P(t) + P(t-1) + ... + P(t-19)) / 20`  
  
  Window: 20 completed ASX trading sessions.  
  Unit: index points.

- **Edge cases:**  
  Do not calculate the metric until 20 valid closing prices are available. Missing or invalid closing prices should not be silently replaced. An incomplete live trading-day value should not be included as a completed session.

- **The question it answers, and why it matters for benchmarking:**  
  This metric answers: **Is the Australian equity market generally trending upward, downward, or sideways?**  
  It gives management a more stable view of market direction than the daily closing price alone and provides a consistent trend measure that could later be compared with the bank's own performance.

## M2 — 20-session realised volatility

- **Definition:**  
  Realised volatility measures how much the S&P/ASX 200 has been moving from day to day over the most recent 20 completed trading sessions. A higher value indicates that recent market conditions have been more unstable.

- **Calculation:**  
  First calculate the daily log return:

  `r(t) = ln(P(t) / P(t-1))`

  Then calculate the standard deviation of the latest 20 valid daily log returns and annualise it:

  `Vol20(t) = standard deviation of the latest 20 returns × √252 × 100`

  Window: 20 valid daily returns.  
  Unit: annualised percentage.

- **Edge cases:**  
  Return `NULL` until there are enough valid observations to form the complete window. Missing or invalid closing prices should not be treated as zero returns. Only completed trading sessions should be included.

- **The question it answers:**  
  This metric answers: **Is the recent market trend occurring under relatively stable or unusually volatile conditions?**  
  This matters because price direction alone does not show how risky or unstable the path has been. Two periods may have similar returns but very different levels of market uncertainty.

## M3 — Australian 10-year yield, 5-observation change

- **Definition:**  
  This metric measures how much the Australian Government 10-year bond yield has changed between the latest valid RBA observation and the fifth previous valid observation. It shows whether longer-term Australian interest-rate conditions are moving materially.

- **Calculation:**  
  Calculate the difference between the latest valid yield and the yield five valid RBA observations earlier:

  `Yield change 5 obs (bp) = (Y(t) - Y(t-5)) × 100`

  Unit: basis points.

  The calculation must be performed on the valid RBA observations **before** the yield series is joined to ASX trading dates.

- **Edge cases (carried/missing days, "as at" date):**  
  Missing RBA observations should not automatically be treated as unchanged yields. If an ASX trading day has no corresponding RBA observation, the analytical yield value remains missing and is flagged. The metric should use only genuine RBA observations when counting back five observations. The source's latest available observation date should be retained so users can see the yield's actual "as at" date.

- **The question it answers:**  
  This metric answers: **Are longer-term Australian interest-rate conditions rising, falling, or remaining broadly stable alongside the equity market?**  
  It provides macroeconomic context for the ASX 200 trend and helps management identify periods when equity-market movement and long-term rate conditions may be moving together or diverging.

## Change control

Any change to a metric definition, formula, window, unit or missing-data treatment requires a version note in this file and a corresponding entry in `CHANGELOG.md`. AI-assisted transformation code must implement the committed definition rather than redefine the metric through code.