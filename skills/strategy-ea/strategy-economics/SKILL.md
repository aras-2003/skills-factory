---
name: strategy-economics
description: Reconcile sourced profit pools, value-driver trees, price-volume-mix bridges and cost bridges with explicit assumptions. Use for unit economics and strategy economics; never infer missing financial inputs or claim causality from descriptive decompositions.
---

# Strategy economics

Require an explicit as-of date, currency and source ID/publication date for each numeric input. Use `engine.py` for aggregate profit pools, sum/product driver-tree checks, exact price-volume-mix bridges and baseline-to-actual cost bridges. The PVM convention is volume, then mix at base prices, then price; explain that another order can allocate interaction effects differently.

Keep units and periods comparable before calculation. Report missing inputs instead of filling them, reject future-dated evidence, and show each reconciliation. A driver tree's arithmetic does not prove causality. Profit-pool size and margin do not establish a defensible advantage, and cost changes do not prove the cause of the change. Reuse existing strategy challenge and capital allocation work for decisions rather than duplicating those specialists.

This is an original candidate. The upstream archives and license manifest are unavailable, so this implementation makes no source-equivalence or reuse claim. Runtime acceptance remains pending.
