# Data use

How each source may be used in this proof of concept, and what would change before Really Big Bank used it in production. Drafted by Claude (AI agent) on 1 Nov 2026 from the pages linked below; the team checks it before it is relied on. Terms can change, so re-read the linked pages before any wider use.

## RBA Statistical Table F2 (Australian Government 10-year bond yield, `FCMYGBAG10D`)

What the RBA's Copyright and Disclaimer Notice says (read 1 Nov 2026, <https://www.rba.gov.au/copyright/>):

- Most RBA material is under CC BY 4.0, but **"RBA Financial Data" is excluded** and has its own terms (section 5). Financial Data covers numerical or statistical information the RBA publishes (other than the cash rate), so F2 falls under section 5.
- Use for personal or commercial purposes is allowed, with attribution in the form **"Source: Reserve Bank of Australia [year]"** or **"Source: RBA [year]"**, and without suggesting that the RBA endorses the use.
- The RBA does **not** administer this data as a financial benchmark and does not recommend using it as one; the user carries the risk of any use.
- The RBA may change or withdraw the data, its methods or its publication schedule without notice, and accepts no responsibility for its accuracy or completeness.

What this project does about it:

| Term | How the project respects it |
| --- | --- |
| Attribution | The dashboard footer and freshness panel name the RBA and Table F2 as the source. The report should use "Source: RBA (2026)" under every figure that shows the yield |
| Not a benchmark | The yield is context for ASX activity (an overlay and a correlation), never a pricing or performance benchmark, and never the trigger for the volume signal |
| May change or be revised | Every new or changed value is kept with the time we first saw it (`data/curated/au10y_vintages.csv`); a changed value is logged as DQ08 |
| Publication schedule may change | The release calendar only sets what we *expect*; a late file is logged as `late`, never filled in |

## Yahoo Finance (S&P/ASX 200 daily bars, `^AXJO`)

- The pipeline reads Yahoo's public chart endpoint (`config/sources.yaml`). As far as we know this is **not an official, documented data service** for third parties, and we have **not verified** that Yahoo's terms of service allow this use. The team should treat it as acceptable only for a university proof of concept, and should check Yahoo's current terms before quoting anything stronger.
- The index level and the S&P/ASX 200 name belong to their owners (S&P Dow Jones Indices and ASX). The dashboard names Yahoo Finance as the source of the bars.
- Known data limits (see `docs/RUNBOOK.md`): Yahoo's index volume is far smaller than the market's traded volume, so it is used **only relative to its own 20-session normal**, never as an absolute number; the newest bar arrives as a live, provisional bar.

**For production at Really Big Bank:** replace Yahoo with a licensed market-data feed the bank already pays for (for example its existing market-data vendor, or ASX data products), keep the same data contract (`config/sources.yaml`) and quality rules, and record the licence in this file.

## Personal information

Neither source contains personal information. The pipeline stores no user or customer data, so the Privacy Act does not bear on the data itself; it would if bank performance data were added for benchmarking later, and that addition should start with a privacy impact assessment.
