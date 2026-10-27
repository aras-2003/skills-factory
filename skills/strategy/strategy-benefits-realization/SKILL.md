---
name: strategy-benefits-realization
description: Track forecast and realized benefits from approved initiatives with ownership, baselines, timing, evidence and reconciliation. Use for benefit realization governance; hand off KPI design, strategy diagnosis, decision rights and capital reallocation to existing OAF skills.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: candidate
  risk: medium
  last_reviewed: "2026-10-27"
---

# Benefits Realization

## Purpose
Maintain an auditable link from approved initiative assumptions to observed benefit evidence and variance decisions.

## Ledger fields
Initiative and hypothesis; accountable owner; benefit metric and unit; baseline value/date/source; forecast value/date; realization window; attribution method; dependencies; costs/investment; actual values with dates and sources; confidence; status; corrective action and decision owner.

## Procedure
1. Link each benefit to an approved strategic outcome and one accountable owner.
2. Freeze a dated baseline before intervention. Define counterfactual/attribution and guardrail metrics; do not claim causality from before-after movement alone.
3. Separate gross benefit, displacement/cannibalization, one-off effects, recurring benefit and implementation cost. Prevent overlap across initiatives.
4. Record forecast and actual on a common unit, period and perimeter. Reconcile variance into volume, price/mix, timing, attribution, cost and external factors; mark unexplained residual.
5. Preserve evidence links and change history. Missing or stale evidence is `UNVERIFIED`, not realized.
6. Escalate material variance against pre-agreed thresholds to the decision owner. Hand off KPI validity to `kpi-quality-review`, execution diagnosis to `strategy-to-execution-diagnostic`, and resource reallocation to `portfolio-prioritization`.

## Output contract
Benefits ledger | forecast-versus-actual bridge | evidence status | variance owner | next review date | escalations. This skill records and reconciles; it does not authorize capital allocation.

## Quality checks
- [ ] Baseline predates intervention and has source/date.
- [ ] Benefit is attributable, net of displacement and costs, or explicitly unverified.
- [ ] Units, perimeter and periods align.
- [ ] Initiative overlap and unexplained residual are visible.
- [ ] Decision rights remain with existing governance.
