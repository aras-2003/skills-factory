---
name: strategy-financial-model
description: Build or audit a generic business cash-flow decision model with explicit assumptions and deterministic NPV, IRR, payback and sensitivity calculations. Use for projects or business cases, not public-security valuation.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: candidate
  risk: high
  last_reviewed: "2026-10-27"
---

# Strategy Financial Model

## Purpose
Evaluate incremental business decisions with reproducible cash-flow arithmetic and explicit input uncertainty.

## Required inputs
Currency, period convention, initial and subsequent cash flows, timing, discount rate, tax treatment if applicable, terminal value basis, and scenario assumptions. Missing decision-critical inputs block a point result.

## Procedure
1. Establish the decision and model boundary; distinguish incremental cash flows from accounting earnings and sunk costs.
2. Record each input with definition, unit, source, date, owner and low/base/high range. Keep formulas separate from inputs.
3. Build scenarios by changing explicit operating drivers, not by applying arbitrary percentage labels to the final value.
4. Calculate NPV with the supplied period convention and discount rate. Calculate IRR only when cash flows admit an economically meaningful root; disclose multiple/no-root cases.
5. Calculate simple payback from cumulative undiscounted cash flows and discounted payback separately when requested. Interpolate within a period only if the convention is stated.
6. Reconcile opening to ending value with an explicit bridge. Run one-way sensitivities and identify interaction risks that one-way analysis misses.
7. Audit units, signs, dates, formula lineage, scenario completeness and invariants. Report rounded display values alongside unrounded calculator results.
8. No probabilities without evidence. Investment security analysis is outside scope: hand off to `valuation-scenario-review`.

## Output contract
Input register | scenario cash-flow schedule | NPV, IRR and payback with conventions | sensitivity table | reconciliation checks | unresolved assumptions and decision threshold.

## Quality checks
- [ ] All cash-flow periods, currency and signs are consistent.
- [ ] NPV includes time-zero flow exactly once.
- [ ] IRR root is checked by plugging it back into NPV.
- [ ] Payback method is labeled and not confused with value creation.
- [ ] Sensitivity ranges are tied to evidence, and missing inputs remain unresolved.
