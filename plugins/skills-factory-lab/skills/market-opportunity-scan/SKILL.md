---
name: market-opportunity-scan
description: 'Screen the XTB-investable equity and ETF universe for research candidates
  using changes in fundamentals, valuation, expectations, price behavior and portfolio
  relevance. Use for broad opportunity hunting or change detection. Prefer installed
  structured equity-research plugins for breadth, Firecrawl/primary sources for verification,
  and canonical portfolio context from investment-record-store. Do not issue buy/sell
  instructions.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.3.1
  maturity: production
  risk: medium
  last_reviewed: '2026-10-09'
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
