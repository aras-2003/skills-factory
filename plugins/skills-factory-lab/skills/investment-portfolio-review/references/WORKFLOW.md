# Investment Portfolio Review Workflow

## Purpose
Review the user's investment portfolio as a system, detect material concentration, diversification/overlap risk, drift or thesis deterioration, and surface only positions that require attention.

## Natural activation
Use this workflow for ordinary portfolio-review requests even when the user does not name the workflow, Investment OS, XTB, canonical storage or any specialist skill. Typical natural requests include:
- "review my portfolio";
- "review this portfolio";
- "what requires attention in my portfolio?";
- a list/table of holdings or weights followed by a request for risk, concentration, diversification or next decisions.

When activated naturally, do not replace the workflow with a generic investment commentary answer. Run the canonical/evidence path first, then integrated reporting and the required visual-floor path. Do not mark the workflow complete until the composition visual slot has a renderer receipt or an explicit `BLOCKED_NO_RENDERER` result.

## Required skills
- portfolio-state-review
- thesis-monitor
- investment-record-store

## Optional skills
- investment-attention-triage
- position-sizing-review
- valuation-scenario-review
- thesis-challenge
- decision-journal-update

## Sequence
1. Attempt canonical reads first through investment-record-store: current_positions, latest portfolio snapshot, current policy, active thesis versions and relevant transaction history. Emit canonical READ receipt.
   - Resolve backend/project/schema from the record-store bootstrap contract first; do not choose a schema by scanning for populated duplicate tables.
   - Treat the schema named in the canonical READ receipt as authoritative for the entire workflow run.
   - If the user also supplied holdings/weights, preserve them as USER_PROVIDED evidence and reconcile them against canonical state when available.
   - Do not skip canonical reads merely because the prompt already contains enough numbers for a generic analysis.
2. If current state or prior snapshot is unavailable, state exactly which comparison is blocked. Do not substitute local/chat/analytics cache.
3. Reconcile current state and preserve append-only snapshot history.
4. Use Data/analytics tooling for concentration, ETF look-through, overlap, currency, theme/cycle and historical trend calculations when useful. Treat results as derived analytics.
5. Attribute change only when evidence supports causality:
   - current state alone cannot establish drift cause;
   - current + prior canonical snapshots establish change, but not necessarily whether it came from trades or market movement;
   - classify trade-driven vs market-driven only when transaction evidence plus comparable prior/current state, or an explicit canonical attribution record, distinguishes the causes;
   - an empty, incomplete or unavailable transaction table is not causal evidence and does not prove that no transaction occurred;
   - otherwise return attribution `UNKNOWN` and do not guess.
6. Triage new company/industry/market evidence with investment-attention-triage.
7. For REVIEW/ESCALATE positions, run thesis-monitor.
8. Revalue only positions where valuation drift can change the action.
9. Use position-sizing-review when concentration, uncertainty or thesis state changes the policy band.
10. Surface only positions requiring action review.
11. Persist new snapshot, signals, thesis-monitor records and user-confirmed decisions through investment-record-store only.
12. Emit canonical WRITE receipt.
13. After analytical synthesis, call `report-composer` and satisfy the required composition/concentration visual slot with a callable renderer. Record `PAYLOAD_RENDERED` or `BLOCKED_NO_RENDERER`; client display is `NOT_OBSERVABLE` unless directly observed. Do not close the workflow with an unreported visual slot.

## Decision rules
- analytics layer reads/derives; it does not become the system of record;
- canonical schema is resolved once through investment-record-store and must not change mid-run;
- duplicate Supabase schemas are not fallback sources;
- position risk can deteriorate while company thesis remains intact;
- no-trade price drift is still portfolio drift;
- policy breach triggers review, not automatic sale;
- without prior canonical snapshot, do not claim a complete change comparison;
- without sufficient transaction/history evidence, do not classify drift as trade-driven or market-driven;
- an empty, incomplete, unavailable or zero-row transaction result is not evidence that no transaction occurred;
- user-provided aggregate metrics that cannot be recomputed from the visible holdings remain USER_PROVIDED, not DERIVED.

## Output contract
Requires attention; no material change; portfolio-level observations; derived analytics/provenance; canonical READ/WRITE receipts.

When change exists but causal evidence does not distinguish transactions from market movement, state that attribution is `UNKNOWN` because distinguishing evidence is insufficient. Do not explain UNKNOWN merely as "the transaction table is empty".

## Stop conditions
Stop when every material alert is tied to evidence or policy.

## Integrated report presentation
Render the report directly in the chat response by default. External HTML/PDF/Figma/deck/file output is allowed only when the user explicitly requests that artifact or format.

After analytical synthesis, call `report-composer` to produce one portfolio decision report. Use `visual-output-design` for inline components only. This step is mandatory for substantial portfolio reviews; do not stop after a prose-only analytical answer when the visual floor applies. Before marking the workflow complete, record the required composition/concentration visual as `PAYLOAD_RENDERED` or `BLOCKED_NO_RENDERER`. Renderer output does not establish that the client displayed it; report display as `NOT_OBSERVABLE` unless directly observed.

Default profile:
- portfolio decision headline + KPI strip;
- concentration/diversification with inline allocation/concentration charts;
- overlap/look-through matrix when supported;
- material drift/change since prior snapshot;
- positions requiring attention;
- opportunity implications;
- decision queue / next actions;
- canonical READ/WRITE receipts and limitations.

Prefer embedded chat-native visual payloads when multiple coordinated portfolio views materially help. Renderer payload success does not prove client display; client display remains NOT_OBSERVABLE to the model. If rendering is unavailable, use truthful tables/structured prose as diagnostic fallback; do not generate an external artifact unless explicitly requested.
