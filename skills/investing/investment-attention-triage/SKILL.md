---
name: investment-attention-triage
description: >
  Triage new market, company, industry and portfolio information into a short attention queue based on materiality,
  thesis impact, valuation/expectations and decision relevance. Use structured research plugins for breadth,
  Firecrawl/primary sources for verification, and canonical Investment OS history for change detection.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.2.3"
  maturity: production
  risk: high
  last_reviewed: "2026-10-09"
  execution:
    default_model_class: standard
---

# Investment Attention Triage

## Purpose
Convert noisy new information into a decision-focused queue: what changed, whether it matters, where to look deeper, and why.

## Procedure
1. Load relevant canonical portfolio, watchlist, thesis, signal history and prior attention state.
2. Use structured equity/ETF research tools for breadth, then retrieve primary evidence for material claims where practical; Firecrawl may be used for live retrieval/parsing.
3. For each item, identify the affected thesis assumption, KPI, catalyst, risk or valuation expectation.
4. Compare the new evidence with the prior thesis/expectation and assess whether it can change a decision. Check the evidence against: revenue/earnings/free-cash-flow, demand/pricing/margins, competitive position, strategic relevance, valuation assumptions, catalyst timing, and thesis invalidation/kill criteria. Use only dimensions relevant to the item; do not turn this into a full company valuation.
5. Classify materiality using exactly one value from `NOISE`, `MONITOR`, `REVIEW`, `ESCALATE`. Preserve the selected enum verbatim in structured output; do not replace it with a synonym or omit the classification. Give a short reason tied to the affected decision assumption.
6. Classify direction separately: STRENGTHENS / WEAKENS / MIXED / NEUTRAL.
7. Assess market reaction and whether the evidence may already be priced in only as interpretations, not proof.
8. State the smallest next research question and specialist path, plus the decision it could change (for example, no action, monitor, or deeper review).
9. For material items, **consider** canonical persistence only after confirming explicit current-user authorization or a specific, verifiable standing write mandate. A request to review, analyze, monitor or summarize information is not permission to write. Honor read-only/no-save/preview/test instructions and unknown environments: do not write, and report `NOT_WRITTEN`. If authorized, delegate only an idempotent material research-state append to the verified canonical target through investment-record-store; never authorize trades, owner decisions, policy changes or thesis activation. Report `SAVED` only with a successful real WRITE receipt; return `WRITE_FAILED` on failure, not an invented saved state.

If the user has not supplied a ticker, the new information, or the prior thesis/expectation, do not stop at an intake form. State a provisional decision rule using the relevant dimensions above, name the exact missing inputs, and ask only for the minimum needed to apply it. Mark the conclusion provisional; do not invent company facts or imply that a materiality assessment has already been completed.

## Decision rules
- Headline size != materiality.
- Research-provider ranking != thesis relevance.
- Price reaction != thesis validation.
- Company good news can coexist with worse valuation.
- Portfolio concentration can raise decision relevance.
- Materiality classification is a research judgment, not write authorization. No canonical side effects without a verified write boundary.
- `NOISE`, `MONITOR`, `REVIEW`, and `ESCALATE` are the complete allowed materiality enum; do not create alternate labels.

## Output contract
For each item assessed, show: what changed versus prior expectation; relevant decision dimension(s); materiality enum with a brief rationale; direction; priced-in view when evidence permits; decision consequence; provenance; next research question and smallest escalation path. Suppress noise. When inputs are missing, show a provisional decision rule and the minimum missing inputs instead of returning only a questionnaire. Include a canonical persistence status (`NOT_WRITTEN`, `SAVED`, or `WRITE_FAILED`); include the actual WRITE receipt only when a write was attempted.

## Quality checks
- [ ] Every queued item says what changed versus prior state/expectation.
- [ ] Materiality is supported by an explicit, decision-linked reason; missing inputs produce a provisional rule rather than an intake-only response.
- [ ] Material claims have dated provenance.
- [ ] Materiality and direction are separate.
- [ ] Persistence routes through investment-record-store.
