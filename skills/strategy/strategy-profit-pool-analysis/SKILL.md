---
name: strategy-profit-pool-analysis
description: Decompose industry or value-chain profit pools and explain structural differences in returns and value drivers. Use for strategy-level economics; hand off offer-level unit economics and portfolio ranking to their existing skills.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: candidate
  risk: medium
  last_reviewed: "2026-10-27"
---

# Strategy Profit Pool Analysis

## Purpose
Explain where economic value accrues across a defined value chain and which mechanisms account for the differences.

## Procedure
1. Bound the industry, geography, customer value chain and period; distinguish revenue from profit and cash flow.
2. Map activities and participant types, including intermediaries and customer-owned alternatives.
3. Estimate each pool with comparable definitions: revenue × operating margin, or invested capital × return on capital where supported. Keep sources, units and years aligned.
4. Separate observed economics from estimates. Reconcile segment totals to industry totals and disclose coverage gaps.
5. Identify structural drivers (scarcity, bargaining power, switching costs, utilization, regulation, asset intensity, risk) and test causality rather than infer it from correlation.
6. Build a value-driver tree from strategic levers to measurable operating drivers to profit/cash outcomes. Specify sign, unit, lag, dependencies and double-counting controls.
7. Use a bridge to reconcile baseline to target. Contributions must sum to the total change; show interaction/residual explicitly rather than allocate it twice.
8. Hand off initiative ranking/capital allocation to `portfolio-prioritization`; hand off offer-level contribution economics to `unit-economics-review`.

## Output contract
Boundary | pool table (revenue, margin, profit, capital/returns where available) | evidence quality | structural drivers | value-driver tree | baseline-to-target bridge | residual | decision implications and gaps.

## Quality checks
- [ ] Revenue, profit, cash and return metrics are not conflated.
- [ ] Periods and accounting definitions are comparable.
- [ ] Pool coverage and reconciliation are explicit.
- [ ] Driver relationships have mechanisms and evidence.
- [ ] Bridge arithmetic reconciles without double counting.
