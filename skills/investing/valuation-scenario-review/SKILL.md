---
name: valuation-scenario-review
description: >
  Build bear, base and bull valuation scenarios for one security using explicit operating assumptions, valuation
  methods and market-implied expectations. Use when valuation could change an investment decision or position size.
  Do not use as a standalone price-target generator.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.3.0"
  maturity: production
  risk: high
  last_reviewed: 2026-10-31
  execution:
    default_model_class: standard
---

# Valuation Scenario Review

## Purpose
Make valuation assumptions visible and test sensitivity instead of producing false precision.

## Procedure
1. Gate on verified, period-aligned inputs and record price, currency, diluted shares, as-of date, source and reporting period. Missing or conflicted critical inputs yield `NOT_SCORED`; never fill gaps with estimates.
2. Select a method appropriate to the business and cycle, and state why alternatives are weaker: normalized EPS/multiple for earnings businesses, NAV for asset developers, FFO/AFFO for REITs, residual income for financials, and normalized FCF/DCF for cash-generative businesses. For a highly levered issuer, show debt and debt-like claims in the equity bridge and test refinancing stress.
3. Build bear/base/bull operating assumptions with an explicit horizon. Scenarios must differ in operating logic, not only the exit multiple.
4. Separate earnings/cash-flow assumptions from terminal or exit assumptions. A tested arithmetic helper is packaged at `scripts/valuation_scenarios.py`; use it only when the active runtime can actually execute packaged scripts. Otherwise show formulas and calculations, and do not claim the helper ran. In either case, include units and the equity bridge; the helper calculates only from supplied inputs and does not choose assumptions.
5. Present one auditable Valuation & Opportunity Card: method and alternatives; as-of price/currency; bear/base/bull fair-value ranges; margin of safety `(fair value - price) / fair value`; upside `(fair value / price) - 1`; horizons; separate quality, valuation, catalyst/timing, portfolio fit and confidence; and source/provenance for every material input.
6. For DCF/FCF methods, recompute FCF ±20% and discount rate ±20% relative to the base rate. For EPS/AFFO, recompute the earnings/FFO per-share input and multiple independently at ±20%. For NAV, recompute asset value and liabilities at ±20%, and price-to-NAV at ±20% when used. Do not label a generic sensitivity as a DCF result.
7. Compare with historical ranges and relevant peers only when definitions and periods are comparable. Estimate what current price implies and identify the assumption driving the valuation range.
8. Do not assign scenario probabilities unless there is an explicit, cited evidence basis. A scenario range is not a probability distribution or a price target.

## Decision rules
- Peak-cycle earnings require normalized scenarios.
- A wide valuation range is information about uncertainty, not a reason to average mechanically.
- Analyst targets are secondary evidence.
- Precision beyond input quality is misleading.
- Margin of safety and upside are distinct calculations; do not substitute one for the other.
- Never display numeric fair value when price, shares, financial inputs, currency, or method-critical definitions are missing or conflicted.
- Keep the card in Tactical Review / underwriting; do not overload the daily Risk Brief or imply an order.

## Output contract
Valuation & Opportunity Card with input status and provenance; method and rejected alternatives; bear/base/bull table; fair value, margin of safety and upside; horizon; separate quality/valuation/catalyst/portfolio fit/confidence; sensitivity; implied expectations; major uncertainty; data gaps; next verification step. When critical inputs fail the gate, return `NOT_SCORED` and the missing evidence instead of a partial numeric card.

## Quality checks
- [ ] Bear/base/bull differ in operating logic, not only multiple.
- [ ] Current price implications are addressed.
- [ ] No unsupported probability weighting.
- [ ] Cyclicality is normalized where relevant.
- [ ] Industry method is justified and equity value reconciles debt-like claims and diluted shares.
- [ ] Margin of safety and upside formulas are independently labelled and calculated.
- [ ] Critical inputs, periods, currency and sources are explicit; missing data blocks scoring.
- [ ] Sensitivity recomputes the underlying method and is not described as a probability.
