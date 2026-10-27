---
name: technical-structure
description: Use as the technical-structure analyst when an investment request concerns confirmed price swings, Dow-style trend state, support/resistance, and invalidation from supplied adjusted OHLCV.
metadata:
  owner: arkadiusz-kamrowski
  version: 0.1.0
  maturity: candidate
  risk: high
  last_reviewed: '2026-10-27'
---

# Technical Structure

## Purpose
Describe observable swing structure and its conditions of confirmation or invalidation. This is a deterministic technical-state summary, not a return forecast, probability, or buy/sell instruction. OPS means the latest confirmed swing high; OPD means the latest confirmed swing low in this implementation. These operational definitions are independent of any proprietary Squaber rule set.

## Required input
Use supplied adjusted OHLCV bars with stable source IDs, observation/publication timestamps, currency, adjustment method, and an as-of timestamp. The bundled engine accepts a single instrument and does not fetch or adjust data. Missing adjustment/provenance or an excessive date gap yields `UNKNOWN`.

## Procedure
1. Confirm chronological unique bars, valid OHLC relationships, adjusted-price declaration, and timestamps no later than as-of.
2. Detect swing highs/lows using explicit left/right bar counts. A pivot becomes visible only at the timestamp of its right-side confirmation bar.
3. Classify structure only when two confirmed highs and lows exist: HH+HL is `UPTREND`; LH+LL is `DOWNTREND`; otherwise `RANGE_OR_MIXED`. With insufficient history, return `UNKNOWN`.
4. Report OPS/OPD levels, confirmation dates, source, distances from current adjusted close, breakout/retest conditions and invalidation. Distinguish observation from interpretation.
5. Optionally add separately sourced volume, moving-average, benchmark-relative-strength or momentum context. Do not treat missing optional confirmations as neutral proof.
6. The deterministic 0–100 structure score encodes only the observed higher-high/higher-low pattern (50 base, +25 for each). It is not probability or evidence of predictive edge. Keep it separate from the Opportunity Score.

## Output contract
For each requested horizon, identify the bar window/parameters, as-of time, trend state, confirmed OPS/OPD price and percentage distance, source IDs, confirmation dates, level-trigger conditions, invalidation and missingness. The engine emits one supplied-window state; it does not independently validate 1–3 month, 6–12 month or >3 year predictive horizons. Never fill a missing pivot or price.

## Limits
No historical instrument corpus, corporate-action processor, market calendar, signal-cost simulation, chart rendering, walk-forward or out-of-sample validation is bundled. Do not claim those have passed. Never automate portfolio changes or trades.
