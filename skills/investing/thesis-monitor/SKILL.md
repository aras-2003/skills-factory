---
name: thesis-monitor
description: >
  Monitor an existing investment thesis against new earnings, guidance, industry data, price/valuation changes and
  predefined kill criteria. Use canonical thesis history plus structured research/primary evidence; do not restart
  full underwriting unless the thesis materially changes or evidence becomes stale.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.3.2"
  maturity: production
  risk: high
  last_reviewed: "2026-10-09"
  execution:
    default_model_class: standard
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
4. Map each material change to the exact thesis assumption, KPI, catalyst, risk or kill criterion.
5. Update valuation/expectations context separately from business-thesis state.
6. Compare market reaction with fundamental change only as interpretation.
7. Detect portfolio implications such as position drift but route sizing decisions to position-sizing-review.
8. Append a monitoring record as a new canonical research/monitoring event through investment-record-store **only** when the user explicitly requested saving it or a verifiable standing authorization covers the exact write; never rewrite thesis history. First prepare the event and confirm the canonical store is available. If write authority is absent, return analysis with persistence `NOT_WRITTEN` instead of making an external change. Report `SAVED` only with an observed successful tool receipt; on a real failure report `WRITE_FAILED` with evidence. Never invent a receipt.
9. Escalate only when evidence justifies deeper work.

## Decision rules
- News importance is measured against thesis, not headline size.
- Research-provider output does not replace canonical thesis history.
- A DRAFT thesis is not an active monitoring baseline.
- No ACTIVE thesis baseline means no thesis-health outcome; do not substitute generic invalidation criteria for the user's actual recorded thesis.
- Price change alone does not prove thesis change.
- Kill criteria require evidence, not narrative discomfort.
- Historical thesis versions remain immutable.
- A request to analyze changes is not, by itself, authorization to modify an external canonical store. Verify the applicable user or standing policy before writing.

## Output contract
What changed; materiality; direction; affected thesis element; valuation/expectations impact; market reaction context; next step; **persistence state** (`SAVED` with verified receipt, `NOT_WRITTEN`, or `WRITE_FAILED`). Never invent a storage receipt. If the canonical baseline could not be retrieved, report `BLOCKED_CANONICAL_READ` rather than a thesis-health judgment.
