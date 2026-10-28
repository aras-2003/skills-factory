---
name: financial-modeling
description: Run deterministic, evidence-bound NPV, DCF, IRR, payback, scenario and sensitivity calculations from explicit supplied inputs.
metadata:
  owner: skills-factory
  version: 0.1.0
  maturity: candidate
  risk: high
  last_reviewed: '2026-10-27'
---

# Financial Modeling

## Purpose
Calculate a declared financial model reproducibly. Separate model architecture and interpretation from formula execution. This capability performs arithmetic; it does not source assumptions, certify a business case, or recommend investment.

## Inputs and evidence
Require one currency, an `as_of` date, explicit equally spaced periods, cash flows including period zero, and a discount rate. Every numeric assumption, including sensitivity values and scenario weights, must carry `source_id` and `published_at` no later than `as_of`. Reject ambiguous period conventions, gaps, future-dated evidence, and missing provenance. Do not silently substitute a tax rate, discount rate, forecast, terminal growth, or scenario weight.

## Procedure
1. Freeze the question, model boundary, currency, period convention, and as-of date.
2. Validate source IDs, publication dates, units, signs, periods, and the discount-rate convention.
3. Use `engine.py` (library or JSON CLI) for exact arithmetic: NPV includes period zero; DCF terminal value is optional and uses Gordon growth only when supplied; IRR is returned only when a unique conventional sign change is present; simple and discounted payback are reported separately. Fractional payback assumes linear realization within the crossing period.
4. Calculate scenario-weighted NPV only from complete scenarios whose explicit weights sum to one. Call the result an explicitly weighted scenario value; weights are not treated as calibrated probabilities.
5. Run sensitivity only across user/evidence-supplied values. Never generate a range automatically.
6. Return formula conventions, source IDs, as-of date, exact outputs, sensitivity/scenario assumptions, and unresolved limitations.

## Safety and interpretation
- Missing or future-dated inputs are errors; do not backfill with current values.
- A model output is not a forecast probability, expected return, valuation recommendation, or approval to spend or invest.
- Taxes, financing structure, working capital, inflation, currency conversion, and risk adjustment are not implied. Add them only when explicitly modeled with sourced inputs.
- A computed scenario-weighted value is not calibrated risk-adjusted value unless weights and scenario construction have independent empirical validation.
- No data retrieval, writes, or external actions are performed by this component.

## Verification boundary
The bundled calculator verifies arithmetic and input contracts on synthetic fixtures. It does not validate source authenticity, forecast quality, legal/accounting treatment, economic assumptions, or runtime behavior. The public source corpus is now hash-verified and used as method reference only. No third-party content is copied or claimed equivalent; runtime acceptance remains pending.
