---
name: market-opportunity-scan
description: >
  Screen the XTB-investable equity and ETF universe for research candidates using changes in fundamentals, valuation,
  expectations, price behavior and portfolio relevance. Use for broad opportunity hunting or change detection.
  Prefer installed structured equity-research plugins for breadth, Firecrawl/primary sources for verification, and
  canonical portfolio context from investment-record-store. Do not issue buy/sell instructions.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.3.1"
  maturity: production
  risk: medium
  last_reviewed: "2026-10-09"
  execution:
    default_model_class: fast
---

# Market Opportunity Scan

## Purpose
Reduce a broad investable universe to a small research queue by looking for meaningful change, not merely popular tickers.

## Tool routing
Use the narrowest available source for each job:
1. **Canonical state**: investment-record-store -> Supabase (or explicit legacy mode before cutover).
2. **Breadth / candidate discovery**: installed structured equity/ETF research plugins such as Public Equity Investing or Stock & ETF Research Panel.
3. **Primary-source verification**: company IR, filings, official ETF pages; use Firecrawl when live retrieval/extraction is useful.
4. **Derived portfolio analytics**: Data plugin or equivalent analytics layer may query canonical data; its output is derived, not canonical.
5. **Google Drive**: raw files/exports only.

Do not treat any research plugin as the canonical portfolio store.

## Procedure
1. Scan globally for interesting equities/ETFs, with XTB availability as a strong preference rather than an initial discovery constraint. Mark broker availability unverified until checked.
2. Load portfolio/watchlist/opportunity/signal history from canonical state so prior ideas are not recycled automatically.
3. Use structured research tools to generate a broad candidate set. Do not overweight names merely because they are already in canonical history.
4. For every candidate, require an explicit **WHY THIS** and **WHY NOW**:
   - what concrete change/event makes this name interesting now;
   - what measurable evidence supports that claim;
   - why this candidate is more interesting than obvious alternatives.
5. Require at least 2-3 decision-relevant measurable signals before promotion beyond raw discovery. Examples: revenue/earnings revision, margin/FCF inflection, backlog/order change, balance-sheet change, utilization/capacity change, valuation compression, pricing change or other sector-specific KPI.
6. Look for valuation dislocation, estimate revisions, margin/FCF inflection, cyclical normalization, quality temporarily mispriced, structural growth and event-driven expectation gaps.
7. Separate:
   - fundamental change;
   - valuation/expectations change;
   - market/price change;
   - catalyst;
   - failure case.
8. Build historical context for promoted candidates:
   - price history: default 5Y when available plus 1Y current setup;
   - key business KPIs: default 12-20 quarters when available;
   - valuation history: default 5Y/full available history where reliable;
   - relevant dated events aligned to major price/fundamental changes.
9. Explain likely drivers of material historical moves using evidence tiers:
   - OBSERVED: price/KPI movement;
   - VERIFIED EVENT: dated earnings/guidance/M&A/regulatory/capex/product event;
   - INTERPRETATION: likely causal link, with confidence;
   - UNKNOWN when evidence does not distinguish causes.
10. Verify decision-relevant claims in primary sources before promotion to the shortlist.
11. Evaluate portfolio relevance and overlap only after the candidate has passed the standalone evidence gate.
12. Remove ideas supported only by cheapness, price decline, momentum, social attention or narrative.
13. Produce a broad research radar of roughly 10-15 candidates, then promote only the best 2-3 to detailed analysis by default. Match the requested coverage; if the evidence or available tools cannot support the minimum breadth or history, state the actual coverage and mark the scan incomplete rather than presenting a partial scan as the full universe.
14. Return an explicit reject/defer rationale for attractive-looking but unsupported names.
15. For a user-requested ranked opportunity comparison, calculate the **Opportunity Score** separately for each requested horizon using the versioned profile below. Score only factor inputs explicitly derived from evidence and carrying source IDs, definition, normalization profile, confidence, quality and as-of date. Do not invent normalized inputs or silently fill missing factors. If a deterministic calculation engine is available, use it; otherwise show the weighted inputs and arithmetic so the result can be independently reproduced. Missing, stale, future-dated, weak-confidence or non-comparable evidence makes that candidate/horizon `NOT_SCORED`; never renormalize remaining weights or substitute 0.50.
16. Rank only candidates with the same horizon, model version, as-of date, factor definitions and compatible normalization profiles. Include score difference to the next candidate and explain material divergence across horizons. Keep portfolio fit/overlap as a separate, post-score assessment; never hide it as a company-score penalty.

## Decision rules
- Discovery can be broad; conviction must be narrow.
- **Cheap is not a thesis. A drawdown is not an opportunity by itself.**
- No candidate reaches the detailed shortlist without WHY THIS, WHY NOW, measurable evidence and a failure case.
- A candidate should not be promoted because it was already found in an earlier run; prior history is context, not a discovery prior.
- Structured research accelerates discovery; primary sources anchor conviction.
- Price up + fundamentals up is not automatically attractive if valuation expanded more.
- Price down + valuation down is not automatically attractive if fundamentals/expectations deteriorated proportionally or worse.
- XTB availability is required before a candidate is called actionable, but not before it can enter the research radar.
- Historical price/KPI moves require evidence-aware attribution; use UNKNOWN instead of a convenient narrative.
- Missing historical series or an unavailable source is a coverage limitation, not a zero-change result. Do not claim a full 5Y or 12–20 quarter analysis unless the dates/periods are present; block promotion when missing history is decision-critical.
- Analytics output cannot overwrite canonical records except through investment-record-store.
- The Opportunity Score is an evidence-backed **research-prioritization index**, not expected return, probability, conviction, fair value or a trade instruction. Its proposed weights and bands are provisional until calibrated on bias-controlled historical data.
- Use model version `opportunity-score-v0.1-provisional`; never compare scores across model versions or incompatible sector/metric normalization profiles.
- Do not score a candidate/horizon unless every required factor below is present, dated no later than shared `as_of`, within its maximum age, confidence >= 0.50, and has at least one source ID and documented normalization profile. Missing evidence is not neutral.
- Keep EPS and FCF quality visible: negative EPS, missing FCF or non-meaningful valuation multiples remain `NOT_SCORED` for the affected required factor unless a documented, sector-appropriate alternative normalization is supported by evidence. Stale consensus blocks the horizon's score; never carry it forward.
- `VERIFIED` requires a primary or otherwise authoritative source and checked definition. `PROVISIONAL` evidence may produce a provisional score for comparison tests, but the only permitted action is `REVIEW_PROVISIONAL`; it cannot enter a production priority queue.
- For fully verified scores, provisional queue thresholds are >=0.65 `PRIORITIZE`, >=0.45 `WATCH`, >=0.25 `DEPRIORITIZE`, otherwise `REJECT`. These are triage thresholds, not calibrated investment truths. For provisional data return `REVIEW_PROVISIONAL`.
- Every score exposes factor values, weights, contributions, definitions, normalization profiles, source IDs, as-of date, confidence, completeness, model version, unrounded/displayed score and `score_is_probability=false`. Keep the verdict to 1–2 sentences and cite the three largest positive/negative contributions plus catalyst/kill criterion; leave the rest for drill-down.
- Test weight sensitivity with a separately named model version. Do not claim historical predictive value, calibration or out-of-sample validation until a no-look-ahead, survivorship-aware backtest with costs and a baseline has run.

## Opportunity Score v0.1 provisional factor profiles

Factor values are already-normalized quality ranks in `[0, 1]` with higher always better; the model does not derive them from raw financial metrics. Each row must retain the normalization method and comparable peer set. A sector-specific value cannot be ranked against another sector until its cross-sector risk adjustment is documented and tested. Weights sum to `1.00` per horizon; never renormalize them after an evidence gate fails.

| Factor | 1–3 months | Max age | 6–12 months | Max age | >3 years | Max age | Required meaning |
|---|---:|---:|---:|---:|---:|---:|---|
| `catalyst_timing` | 0.22 | 45d | — | — | — | — | Dated, verified catalyst relevance and proximity, net of event risk. |
| `estimate_revisions` | 0.18 | 90d | 0.18 | 120d | — | — | Direction and breadth of consensus revisions using a stated EPS/FCF definition and timestamped consensus snapshot. |
| `valuation_expectations` | 0.15 | 90d | 0.22 | 180d | 0.16 | 180d | Valuation relative to normalized growth/FCF and expectations, using comparable definitions; negative EPS or absent FCF cannot be silently mapped to a cheapness score. |
| `price_setup` | 0.15 | 30d | — | — | — | — | Dated price/trend setup and risk/reward context, not a return forecast. |
| `scenario_asymmetry` | 0.20 | 90d | 0.23 | 180d | — | — | Evidence-backed upside/downside scenario balance including horizon-specific costs and risks; scenario ranges are not probabilities. |
| `cycle_resilience` | 0.10 | 180d | 0.10 | 365d | 0.10 | 730d | Resilience through the relevant business/commodity cycle, with cycle position explicit. |
| `business_quality` | — | — | 0.17 | 365d | 0.22 | 365d | Durability of economics, governance and competitive position supported by dated operating evidence. |
| `risk_resilience` | — | — | 0.10 | 180d | — | — | Balance of company-specific, financial, regulatory and event risks relevant to the horizon. |
| `growth_durability` | — | — | — | — | 0.24 | 365d | Long-run demand, growth runway and execution durability, separated from valuation. |
| `reinvestment_returns` | — | — | — | — | 0.18 | 365d | Evidence that reinvestment can earn attractive incremental returns; do not substitute revenue growth alone. |
| `balance_sheet_resilience` | — | — | — | — | 0.10 | 180d | Liquidity, leverage, maturities and downside funding resilience. |

The displayed score is `round-half-up(sum(weight × factor_value), 2)` and must retain the unrounded result. Confidence is the weight-normalized mean factor confidence, multiplied by `1.00` for VERIFIED and `0.70` for PROVISIONAL evidence. Completeness is the sum of valid factor weights. The baseline implementation fails closed unless completeness is `1.00`; the latter two fields are audit metadata, not missing-data compensation.

## Output contract
For the broad radar:
Ticker | WHY THIS | WHY NOW | 2-3 measurable signals | valuation/expectations context | main failure case | portfolio overlap | XTB status | evidence quality | next research step.

For the top 2-3 promoted candidates additionally:
- 5Y price context + 1Y setup when available;
- 12-20 quarter KPI history when available;
- valuation history where reliable;
- dated event timeline;
- observed move vs likely cause with confidence;
- strongest countercase;
- exact reason this name outranked alternatives.
- For each requested horizon, include `rank | candidate | score (0.00–1.00) | difference to next | confidence | completeness | research action | concise verdict`. Keep `NOT_SCORED` visible with evidence-gate reasons and no rank.
- Include a compact score audit with model version, shared as-of date, factor weights/contributions, normalization-profile compatibility, sources and the strongest fact or valuation level that would change the verdict. State explicitly that the score is not a probability.

## Quality checks
- [ ] Canonical portfolio/watchlist context was attempted.
- [ ] New discovery was not limited to names already present in canonical history.
- [ ] Every promoted candidate has explicit WHY THIS and WHY NOW.
- [ ] Every promoted candidate has at least 2-3 measurable decision-relevant signals.
- [ ] Cheapness or drawdown alone cannot promote a candidate.
- [ ] Historical price/KPI context is included for detailed candidates when data are available.
- [ ] Historical causal interpretation is separated from observed facts/events and has confidence or UNKNOWN.
- [ ] Fundamental, valuation and trend signals are distinct.
- [ ] Decision-relevant claims were verified or marked unverified.
- [ ] No candidate is labeled a buy.
- [ ] Broker availability status is explicit.
