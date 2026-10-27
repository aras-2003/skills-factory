---
name: strategy-economics
description: Reconcile sourced profit pools, value-driver trees, price-volume-mix bridges and cost bridges with explicit assumptions. Use for unit economics and strategy economics; never infer missing financial inputs or claim causality from descriptive decompositions.
metadata:
  owner: Skills Factory
  version: 0.1.0
  maturity: candidate
  risk: medium
  last_reviewed: "2026-10-27"
---

## Purpose

Require an explicit as-of date, currency and source ID/publication date for each numeric input. Use `engine.py` for aggregate profit pools, sum/product driver-tree checks, exact price-volume-mix bridges and baseline-to-actual cost bridges. The PVM convention is volume, then mix at base prices, then price; explain that another order can allocate interaction effects differently.

## Procedure

Keep units and periods comparable before calculation. Report missing inputs instead of filling them, reject future-dated evidence, and show each reconciliation. A driver tree's arithmetic does not prove causality. Profit-pool size and margin do not establish a defensible advantage, and cost changes do not prove the cause of the change. Reuse existing strategy challenge and capital allocation work for decisions rather than duplicating those specialists.

## Output

Return sourced totals, margin denominator, the driver-tree reconciliation, the PVM convention and effects, and cost-bridge deltas. Flag incompatible scopes or missing evidence instead of aggregating them. The public source corpus is now hash-verified. It is used as method reference only; no third-party text or code is copied and no source-equivalence claim is made. Runtime acceptance remains pending.
