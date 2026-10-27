---
name: strategy-market-sizing
description: Estimate a defined market for a strategic decision using explicit scope, independent top-down and bottom-up approaches, and evidence-backed ranges. Use for TAM/SAM/SOM and segmentation; hand off cross-market transferability to market-transferability-review.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: candidate
  risk: medium
  last_reviewed: "2026-10-27"
---

# Strategy Market Sizing

## Purpose
Produce a decision-useful market range, not a large unsupported headline.

## Required inputs
Decision, geography, customer, use case, unit of demand, time period, value basis (revenue, units or spend), and as-of date. If any boundary changes the answer materially, request it or show separate cases.

## Procedure
1. Define TAM as all demand meeting the stated need; SAM as demand reachable under the stated product, geography and channel constraints; SOM as a time-bounded attainable share constrained by capacity and route to market.
2. Build a top-down estimate from a dated, scoped source, exposing every adjustment from reported market to target market.
3. Independently build bottom-up demand as eligible entities × incidence/usage × units × net price; show each input, source, unit and period.
4. Reconcile the two methods. Investigate scope, channel, price and denominator differences; do not average unexplained disagreement.
5. Segment on decision-relevant needs, willingness to pay, access or economics. Keep segments mutually exclusive when summing; show overlap otherwise.
6. For whitespace, compare unmet need and current alternatives with evidence of reachability and economics. A gap in a competitor map alone is not demand.
7. Return low/base/high ranges with drivers and sensitivities. Mark unknowns; do not convert unknown to zero or present an unsupported point estimate.
8. State the cheapest next evidence test and the decision threshold it could change.

## Output contract
Scope | TAM/SAM/SOM ranges | top-down bridge | bottom-up equation | segment table | reconciliation | sensitivities | evidence/as-of | unresolved assumptions | next test.

## Boundaries
Market size is not revenue forecast, market share forecast or proof of attractiveness. Currency, price basis and period must match. Hand off local-market transfer questions to `market-transferability-review`.

## Quality checks
- [ ] Scope, unit, geography, time period and value basis are explicit.
- [ ] Top-down and bottom-up calculations are independent and reproducible.
- [ ] SOM has an explicit horizon and capacity/channel constraint.
- [ ] Segment totals do not double count.
- [ ] Sources, assumptions and uncertainty are visible.
