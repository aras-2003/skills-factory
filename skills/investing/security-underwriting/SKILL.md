---
name: security-underwriting
description: >
  Underwrite one equity or ETF as an investment using structured equity research for breadth and primary filings/IR
  for decision-critical verification, then analyze economics, financial quality, growth drivers, valuation, catalysts,
  risks, variant perception and thesis invalidation. Do not use for broad market scanning.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.5.1"
  maturity: production
  risk: high
  last_reviewed: "2026-10-09"
  execution:
    default_model_class: strong
---

# Security Underwriting

## Purpose
Produce an evidence-backed investment case that can later be challenged, valued, sized and monitored.

## Research routing
- Use structured equity/ETF research plugins for fast context, estimates, peer framing and screening.
- For decision-critical financial metrics, prefer company filings, IR releases, official ETF/provider data and regulators.
- Use Firecrawl to retrieve/parse primary pages or filings when helpful.
- Use canonical prior thesis/portfolio context from investment-record-store.
- Research-provider outputs are evidence inputs, never canonical portfolio state.

## Procedure
1. Define instrument, thesis horizon and current as-of date.
2. Load prior thesis/research/portfolio context when available.
3. State **WHY THIS / WHY NOW** before the full underwriting:
   - what specific change or setup caused this security to deserve attention now;
   - which measurable signals support it;
   - why it is preferable to obvious alternatives.
4. Build historical context before current-state interpretation:
   - price: default 5Y when available plus 1Y current setup;
   - fundamentals: default 12-20 quarters for the KPIs that actually drive this business;
   - valuation: default 5Y/full reliable history where available;
   - dated material events aligned to major changes.
5. Explain business model, segment economics, competitive position and capital intensity.
6. Review revenue, margins, cash flow, ROIC/returns, balance sheet, dilution and capex using dated sources.
7. Run a hard evidence-sanity gate on every decision-critical reported metric before any valuation or sizing:
   - verify the exact metric in primary-source context where possible;
   - confirm period, units, currency, GAAP/non-GAAP basis, quarterly vs annual basis, per-share vs absolute values and arithmetic consistency;
   - compare magnitude against adjacent disclosures and prior-period/company scale;
   - extraordinary values trigger re-verification, not automatic rejection;
   - mark unresolved conflicting/extraction-uncertain figures UNVERIFIED or CONFLICTED.
8. If any decision-critical metric remains UNVERIFIED/CONFLICTED:
   - classify research state as VERIFY / RESEARCH;
   - do not compute P/E, FCF yield, numeric valuation scenarios or numeric sizing from those figures;
   - state exactly what must be verified next.
   - If an event, company-specific fact, or key input remains unresolved, identify it as a blocking uncertainty and limit downstream conclusions; do not bury it in a generic risk list or continue to a definitive thesis/valuation conclusion.
9. Only after the evidence gate passes, identify growth/cycle drivers and consensus expectations. Classify business lifecycle with the deterministic `scripts/business_lifecycle.py` classifier and `references/business-lifecycle.md` contract when three comparable annual/TTM observations are available. Report phase and uncalibrated affinity separately from valuation. For insufficient or conflicted inputs, show NOT_CLASSIFIED, not invented phase odds.
10. Evaluate valuation relative to history, peers and scenario economics.
11. Explicitly separate business-thesis strength, security attractiveness at the current price and priced-in expectations.
12. State catalysts, risks, dependencies and variant perception.
13. Form a compact thesis with explicit assumptions and kill criteria.
14. Hand off conviction challenge to thesis-challenge before portfolio action.

## Historical attribution
For material historical price/fundamental moves, separate:
- **OBSERVED** — what the price/KPI actually did;
- **VERIFIED EVENT** — dated earnings, guidance, investment, financing, product, regulatory, M&A or other evidence;
- **INTERPRETATION** — the most plausible causal explanation supported by the timing and evidence;
- **CONFIDENCE** — HIGH / MEDIUM / LOW;
- **UNKNOWN** — when competing explanations cannot be distinguished.

Do not write "the stock fell because X" merely because X happened nearby in time.

## Decision rules
- Cheapness, low multiple or a large drawdown is never sufficient investment rationale by itself.
- Source existence is not evidence that an extracted metric is correct.
- Structured research is a speed layer, not a substitute for primary-source verification of critical figures.
- Extreme numbers may be real; verify before accepting or rejecting them.
- Good business != good security at any price.
- A cheap multiple can reflect peak earnings.
- Never pass UNVERIFIED/CONFLICTED critical metrics into valuation or sizing.

## Visual lifecycle contract
- For every individual equity security review include an **inline graphical Business Lifecycle panel** with all five phases visible, the selected phase highlighted, phase-affinity bars and an explicit **NOT calibrated probability** legend. Produce it from the same classifier output via `scripts/business_lifecycle_visual.py`, not from manually assigned scores.
- When verified comparable financial data are missing, display the five-phase graphic with **NOT CLASSIFIED**, no highlighted phase and N/A bars; never fabricate a phase.
- If a supported renderer is unavailable, display a faithful five-phase text/table equivalent and label `BLOCKED_NO_RENDERER`; never pretend an SVG was rendered.
- Keep the lifecycle panel adjacent to revenue, operating-profit and FCF trends, and visually separate it from valuation and BUY/SELL decision.

## Output contract
WHY THIS / WHY NOW; historical price context; historical KPI trends; historical valuation context; event timeline; observed moves vs likely causes with confidence; business; financial quality; evidence-sanity status; verified/blocked metrics; drivers; business-thesis strength; valuation context if permitted; priced-in expectations; security attractiveness; catalysts; risks; variant perception; thesis; assumptions; kill criteria; exact verification requirements; confidence; provenance.

## Quality checks
- [ ] Prior canonical context was attempted when relevant.
- [ ] WHY THIS / WHY NOW is explicit and evidence-backed.
- [ ] Current and historical evidence are dated.
- [ ] Price history and key KPI history were attempted at the default horizons.
- [ ] Material historical moves separate observation, verified event and causal interpretation/confidence.
- [ ] Critical metrics were independently verified in primary-source context.
- [ ] Extreme values were verified rather than rejected merely for magnitude.
- [ ] No valuation or sizing was computed from blocked metrics.
- [ ] Business thesis and security attractiveness are separate.
- [ ] Kill criteria are falsifiable.
- [ ] Lifecycle graphic or explicitly blocked fallback rendered from verified classifier output, with five phases and uncalibrated-affinity warning.
