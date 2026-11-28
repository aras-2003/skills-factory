---
name: thesis-monitor
description: 'Monitor an existing investment thesis against new earnings, guidance,
  industry data, price/valuation changes and predefined kill criteria. Use canonical
  thesis history plus structured research/primary evidence; do not restart full underwriting
  unless the thesis materially changes or evidence becomes stale.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.4.0
  maturity: production
  risk: high
  last_reviewed: '2026-11-10'
---

# Thesis Monitor

## Purpose
Evaluate what changed versus the recorded thesis rather than summarizing news from scratch.

## Procedure
1. Load the latest ACTIVE canonical thesis version from `current_theses` and prior monitoring state through investment-record-store.
   - Do not use `draft_theses` as an active thesis.
   - If the canonical store is unavailable, return `BLOCKED_CANONICAL_READ`; do not treat an unavailable query as proof that no ACTIVE thesis exists. Do not produce a thesis-health outcome from substitute provider summaries.
   - If only a DRAFT exists or no ACTIVE baseline exists, stop before collecting direction-of-thesis conclusions. Return `BLOCKED_THESIS_NOT_ACTIVE`, state that monitoring outcome is not run, and identify the activation/baseline requirement. Do not label the thesis STRENGTHENED, WEAKENED, intact, or healthy.
2. Gather new dated evidence using structured research tools for breadth and primary sources for material claim verification.
3. Classify materiality separately from direction: NOISE / MONITOR / REVIEW / ESCALATE and STRENGTHENS / WEAKENS / MIXED / NEUTRAL.
4. Map each material change to the exact thesis assumption, KPI, catalyst, risk or kill criterion. Compare a KPI only with its predeclared definition, basis, period, verified baseline, threshold/comparator and rolling window. Missing thresholds are `NOT_SET`; missing or non-comparable evidence is `UNVERIFIED`, not a crossing.
5. Use the trigger row's action class (`MONITOR`, `REVIEW`, or `ESCALATE`). A threshold crossing can start review/escalation only; it does not automatically invalidate a thesis, change canonical state, or authorize a trade. A verified breach of a pre-approved kill criterion escalates for human judgment. Never invent a generic replacement if the ACTIVE thesis has no trigger row.
6. Build a dated expectations bridge when earnings or guidance changed: pre-event consensus, any timestamped revision, reported actual and company guidance. Record each source and publication/retrieval timestamp, fiscal period, metric definition, accounting basis, unit/currency and as-of availability. Keep non-like-for-like periods or GAAP/adjusted definitions separate. Missing, stale, conflicted or future-published evidence remains `UNKNOWN`/`N/M`; do not impute it or use it in a historical decision-time view.
7. Update valuation/expectations context separately from business-thesis state. Assess whether original assumptions were supported, contradicted or unresolved and whether the current business case remains economically attractive; do not use stock return alone as the thesis verdict.
8. Compare market reaction with fundamental change only as interpretation: state the observed move and event window, then label any causal explanation `INTERPRETATION` with confidence and supporting evidence. If evidence does not distinguish alternative causes, report `UNKNOWN`.
9. Detect portfolio implications such as position drift but route sizing decisions to position-sizing-review.
10. Append a monitoring record as a new canonical research/monitoring event through investment-record-store **only** when the user explicitly requested saving it or a verifiable standing authorization covers the exact write; never rewrite thesis history. First prepare the event and confirm the canonical store is available. If write authority is absent, return analysis with persistence `NOT_WRITTEN` instead of making an external change. Report `SAVED` only with an observed successful tool receipt; on a real failure report `WRITE_FAILED` with evidence. Never invent a receipt.
11. Escalate only when evidence justifies deeper work.

## Decision rules
- News importance is measured against thesis, not headline size.
- Research-provider output does not replace canonical thesis history.
- A DRAFT thesis is not an active monitoring baseline.
- No ACTIVE thesis baseline means no thesis-health outcome; do not substitute generic invalidation criteria for the user's actual recorded thesis.
- Price change alone does not prove thesis change.
- Review triggers do not automatically invalidate a thesis or authorize a trade.
- Kill criteria require a verified breach of the pre-approved criterion, not narrative discomfort or a retrospective threshold.
- A missing ACTIVE thesis blocks use of any trigger matrix; never invent a substitute.
- Historical replay uses only evidence published by each decision timestamp; later actuals are outcomes, not decision inputs.
- Separate reported actuals, guidance revisions, expectation revisions, valuation-multiple changes and market reaction.
- Historical thesis versions remain immutable.
- A request to analyze changes is not, by itself, authorization to modify an external canonical store. Verify the applicable user or standing policy before writing.

## Output contract
What changed; materiality; direction; affected thesis element; trigger-matrix row and action class (or explicit `NOT_SET`/`UNVERIFIED`); expectations bridge with source/time/period/basis or explicit gap; observed price move versus uncertain attribution; assessment of original assumptions and current economic attractiveness; next verification; **persistence state** (`SAVED` with verified receipt, `NOT_WRITTEN`, or `WRITE_FAILED`). Never invent a storage receipt. If the canonical baseline could not be retrieved, report `BLOCKED_CANONICAL_READ` rather than a thesis-health judgment.
