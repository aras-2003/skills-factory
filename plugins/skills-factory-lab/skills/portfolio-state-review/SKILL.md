---
name: portfolio-state-review
description: 'Reconstruct and review the current investment portfolio plus historical
  snapshots, exposures and material changes from canonical Investment OS data. Use
  when assessing concentration, diversification, overlap, cash deployment, risk changes
  or what changed since a prior snapshot. Prefer relational Supabase views and analytics
  over spreadsheet logic.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.7.1
  maturity: production
  risk: high
  last_reviewed: '2026-10-09'
---

# Portfolio State Review

## Purpose
Turn canonical holdings/history into a decision-useful portfolio state while preserving auditability.

## Procedure
1. Use investment-record-store to read canonical `current_positions`, latest portfolio snapshot, current policy and relevant exposure data.
2. If the configured canonical backend or prior snapshot is unavailable, state exactly what comparison is blocked. Do not substitute chat/local files or analytics cache.
3. Reconcile position, quantity, cost basis, market value, portfolio weight, account and currency.
   - Return a row-level view for each holding with the available quantity, market value, weight, account, currency, and as-of date; name each missing field rather than silently omitting affected rows. Show prior-period/history rows only when the corresponding snapshot was actually retrieved.
4. Use Data/analytics tooling when useful for aggregation, look-through, concentration, overlap and historical trend analysis; treat all outputs as derived analytics.
5. Review single-name, sector/theme, geography, currency, factor/cyclicality and ETF/stock overlap where supported.
   - For coverage statements, prefer `portfolio_exposure_source_coverage`.
   - "source coverage" means current portfolio weight attached to instruments with any exposure metadata.
   - Do not infer decomposition completeness from source coverage, exposure row counts, or sums across heterogeneous exposure types.
   - Never sum `holding_weight` and `sector_weight` weighted exposures into one coverage percentage.
6. For observation requests, prefer the canonical `portfolio_position_changes` view for latest-valid versus previous-valid snapshot comparison. It establishes observed state only; it does not establish cause.
7. Classify each observed position/exposure state when useful:
   - REQUIRES_ATTENTION;
   - MONITOR;
   - NO_MATERIAL_CHANGE;
   - DATA_GAP.
   Keep this classification separate from thesis direction and from policy enforcement.
8. Compare with the previous canonical snapshot. Attribute causes only when the evidence distinguishes them:
   - use transaction history plus comparable prior/current state, or an explicit canonical attribution record;
   - if prior state is missing, change comparison is blocked;
   - if transaction/cause evidence is incomplete, attribution is `UNKNOWN`;
   - an empty or zero-row transaction result is still incomplete causal evidence unless independent evidence establishes that no transactions occurred;
   - never infer "market-driven", "no-trade" or "no transaction occurred" from the absence of observed transaction data.
9. Treat soft reference bands as observation heuristics only unless the active canonical policy explicitly defines a hard rule. A soft trigger is not a breach and does not imply rebalancing.
10. Flag explicit canonical policy breaches or review thresholds when they truly exist; do not automatically translate a breach into a sell action.
11. Persist a new snapshot/event through investment-record-store only when explicitly authorized by the user or this workflow's declared contract. A review/report request alone is not authorization. Never write during evaluation, a controlled test, preview, or an unknown write boundary; use a verified isolated test store or read-only mode.
12. Return explicit canonical read receipts and, only when an authorized write was attempted, a write receipt.

## Decision rules
- A good company can become a poor portfolio position through concentration.
- Price appreciation that increases weight is a portfolio change even without a transaction.
- Current views and historical snapshots are different records.
- Missing prior canonical state means no claim of "change since prior snapshot."
- Prior/current snapshots can establish that weights changed, but causal attribution requires transaction/cause evidence.
- Absence of a transaction record, including an empty or zero-row canonical query result, is not proof that no transaction occurred.
- User-provided metrics remain USER_PROVIDED unless the workflow can reproduce them from identified inputs.
- Analytics calculations are reproducible derived state, not canonical truth by themselves.
- Observed change and causal attribution are separate outputs.
- Soft reference bands are descriptive attention signals, not target allocations.
- Observation should suppress unchanged/noise items rather than forcing action from a static portfolio structure.
- Source coverage and look-through decomposition completeness are different measures and must not be conflated.

## Output contract
As-of date; canonical-read status; reconciled portfolio summary; material exposures; observed changes since prior snapshot or explicit comparison block; causal attribution or UNKNOWN; observation state (REQUIRES_ATTENTION / MONITOR / NO_MATERIAL_CHANGE / DATA_GAP) where useful; explicit policy exceptions only when canonical policy supports them; stale/missing data; analytics provenance; canonical persistence receipt.

## Quality checks
- [ ] Canonical current state and prior snapshot were attempted.
- [ ] Derived analytics are labeled separately from canonical records.
- [ ] Trade-driven and market-driven changes are separated only when causal evidence is sufficient; otherwise attribution is UNKNOWN.
- [ ] Historical state is not overwritten.
- [ ] Persistence writes route only through investment-record-store.
- [ ] A review/report request alone did not trigger a canonical write.
- [ ] Controlled tests and previews did not modify canonical state.
