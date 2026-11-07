---
name: valuation-scenario-review
description: 'Build bear, base and bull valuation scenarios for one security using
  explicit operating assumptions, valuation methods and market-implied expectations.
  Use when valuation could change an investment decision or position size. Do not
  use as a standalone price-target generator.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.3.2
  maturity: production
  risk: high
  last_reviewed: '2026-11-07'
---

# Valuation Scenario Review

## Purpose
Make valuation assumptions visible and test sensitivity instead of producing false precision.

## Procedure
1. Gate on verified, period-aligned inputs and record price, currency, diluted shares, as-of date, source and reporting period. Use only facts published on or before the selected as-of timestamp; a period-end date does not prove the information was available then. Exclude later publications from that valuation snapshot. Missing or conflicted critical inputs yield `NOT_SCORED`; never fill gaps with estimates.
2. Select a method appropriate to the business and cycle, and state why alternatives are weaker: normalized EPS/multiple for earnings businesses, NAV for asset developers, FFO/AFFO for REITs, residual income for financials, and normalized FCF/DCF for cash-generative businesses. For a highly levered issuer, show debt and debt-like claims in the equity bridge and test refinancing stress.
3. Build bear/base/bull operating assumptions with an explicit horizon. Scenarios must differ in operating logic, not only the exit multiple.
4. Separate earnings/cash-flow assumptions from terminal or exit assumptions. A tested arithmetic helper is packaged at `scripts/valuation_scenarios.py`; use it only when the active runtime can actually execute packaged scripts. Otherwise show formulas and calculations, and do not claim the helper ran. In either case, include units and the equity bridge; the helper calculates only from supplied inputs and does not choose assumptions.
5. Present one auditable Valuation & Opportunity Card: method and alternatives; as-of price/currency; bear/base/bull fair-value ranges; margin of safety `(fair value - price) / fair value`; upside `(fair value / price) - 1`; horizons; separate quality, valuation, catalyst/timing, portfolio fit and confidence; and source/provenance for every material input.
6. For DCF/FCF methods, recompute FCF ±20% and discount rate ±20% relative to the base rate. For EPS/AFFO, recompute the earnings/FFO per-share input and multiple independently at ±20%. For NAV, recompute asset value and liabilities at ±20%, and price-to-NAV at ±20% when used. Do not label a generic sensitivity as a DCF result.
7. Compare with historical ranges and relevant peers only when definitions and periods are comparable. Include comparable EV/sales, EV/EBITDA, forward P/E, revenue/FCF growth, gross/operating/FCF margins, ROIC, dilution and capital intensity when source data support them. Show consensus revisions and historical-multiple context only when they are dated and definition-compatible; otherwise state the data gap. P/S divided by revenue growth is an optional heuristic, never a primary rank. A peer must match sector, industry, as-of date and a reviewed economic comparison group; record a specific inclusion rationale and reviewer-assigned `DIRECT` or `ADJACENT` tier for every included issuer. A `DIRECT` tier needs independent support for whole-company economic fit across value-chain role, material revenue/profit mix, customers, cyclicality and capital intensity; product competition alone is insufficient. Business-model labels remain descriptive and cannot silently determine the tier. A materially different model may appear only as an explicitly justified `ADJACENT` product/segment reference: keep its sourced observations visible, but do not let it enter direct-peer medians, percentiles, PEG or P/S-growth heuristics. Align periods and accounting bases only through explicit reviewer-defined groups that preserve the raw dates/bases in the output; currencies may differ only for dimensionless fractions or multiples. Unmatched or stale values are N/M. A compact direct-peer table needs at least three direct peers and at least one compatible core valuation metric (EV/sales, EV/EBITDA or forward P/E) supported by three peers; peer count alone does not establish comparability. Descriptive percentiles need at least five peers in the reviewed direct cohort. Use PEG = forward P/E / EPS CAGR in percentage points only when both are positive and sourced on the same snapshot. PEG=1 is a heuristic reference, never proof of cheapness or a buy signal. Flag explicitly identified cyclical issuers; never infer cyclicality from a ticker. Separate multi-year EPS growth from 1–3 month catalysts and revisions. Estimate what current price implies and identify the assumption driving the valuation range.
   - When P/S and compatible positive revenue growth exist, the helper may show `P/S / revenue growth in percentage points` as `ps_growth_heuristic`. It stays outside percentiles/ranking and is never a recommendation.
   - use packaged `scripts/peer_comparison.py` only for caller-reviewed facts when the runtime exposes code execution. The optional static scatter is `scripts/peer_growth_plot.py` and must consume the returned comparison snapshot; do not claim either helper ran unless the runtime provides that exact code path.
8. Do not assign scenario probabilities unless there is an explicit, cited evidence basis. A scenario range is not a probability distribution or a price target.

## Decision rules
- Peak-cycle earnings require normalized scenarios.
- A wide valuation range is information about uncertainty, not a reason to average mechanically.
- Analyst targets are secondary evidence.
- Precision beyond input quality is misleading.
- Margin of safety and upside are distinct calculations; do not substitute one for the other.
- Never display numeric fair value when price, shares, financial inputs, currency, or method-critical definitions are missing or conflicted.
- Separate company quality from price attractiveness. Never rank unlike businesses or present a PEG reference as a recommendation.
- Keep the card in Tactical Review / underwriting; do not overload the daily Risk Brief or imply an order.

## Output contract
Valuation & Opportunity Card with input status and provenance; method and rejected alternatives; bear/base/bull table; fair value, margin of safety and upside; horizon; separate quality/valuation/catalyst/portfolio fit/confidence; sensitivity; implied expectations; major uncertainty; data gaps; next verification step. When critical inputs fail the gate, return `NOT_SCORED` and the missing evidence instead of a partial numeric card.

When peer comparison is requested, include inclusion/exclusion rationale and the metric's dated period/basis/definition/source, FCF yield and quality/context fields when available, historical-multiple range and consensus revisions when reliable, and explicit N/M explanations for gaps. Label the peer screen as descriptive context separate from the valuation scenarios and any recommendation.

## Quality checks
- [ ] Bear/base/bull differ in operating logic, not only multiple.
- [ ] Current price implications are addressed.
- [ ] No unsupported probability weighting.
- [ ] Cyclicality is normalized where relevant.
- [ ] Industry method is justified and equity value reconciles debt-like claims and diluted shares.
- [ ] Margin of safety and upside formulas are independently labelled and calculated.
- [ ] Critical inputs, periods, currency and sources are explicit; missing data blocks scoring.
- [ ] Every input's publication timestamp is at or before the valuation as-of timestamp; later publications are excluded.
- [ ] Peer table and optional growth-versus-forward-P/E plot use the same dated snapshot, filters and source-backed points; incompatible inputs are N/M.
- [ ] Sensitivity recomputes the underlying method and is not described as a probability.
