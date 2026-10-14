# Investment Attention Review Workflow

## Purpose
For actionable security follow-up, v1 remains constrained to the XTB-investable universe; non-XTB existing holdings may still be monitored for thesis and portfolio implications.

Answer: **what changed since the last review, what actually matters, and where is deeper research worth the time?** It is not a news digest.

## Entry criteria
Enter for a materiality/attention triage across existing holdings, active theses or a watchlist. Ask for the minimum missing baseline when no verified canonical snapshot is available; do not convert inability to read a store into absence of a thesis.
A single security valuation, original thesis creation or position-sizing decision belongs to its specialist. Default to read-only; persistence is a separate gated operation, not part of the definition of "review".

## Required skills
- investment-attention-triage
- investment-record-store

## Optional skills
- thesis-monitor
- market-opportunity-scan
- trend-theme-research
- security-underwriting
- valuation-scenario-review
- thesis-challenge
- portfolio-state-review

## Sequence
1. Read canonical current portfolio, watchlist, active thesis versions, themes and recent signals. If the canonical baseline is unavailable, report monitoring execution `BLOCKED_CANONICAL_READ`; do not infer that no ACTIVE thesis exists. A user-supplied synthetic ACTIVE fixture remains provisional evidence, not a successful canonical read. You may give a conditional materiality rule and next research question, but no thesis-health judgment.
2. Use structured equity/ETF research plugins for breadth across tracked names.
3. Gather only new dated company, industry, earnings/guidance, estimate, regulatory and relevant market evidence since the last review.
4. Verify material claims in primary sources; use Firecrawl where useful.
5. Run investment-attention-triage and suppress ordinary news.
6. For holdings, use thesis-monitor when a material event maps to an assumption/kill criterion; use valuation-scenario-review when price/expectations changed enough.
7. For new candidates, use market-opportunity-scan; underwrite only REVIEW/ESCALATE items.
8. Use thesis-challenge when confirmation bias or priced-in risk is material.
9. Evaluate whether material signals, evidence links and attention state warrant canonical persistence, but write only with explicit user authorization or a specific verified standing mandate for this workflow and target. A request to review or monitor information alone does not authorize an external write. Honor no-save, read-only, preview, test and unknown-write-boundary modes with `NOT_WRITTEN`. For authorized writes, use investment-record-store, preserve append-only history and report `SAVED` only after an actual successful WRITE receipt; otherwise `WRITE_FAILED`. Before retrying a failed append, check idempotency and whether a partial write exists; do not blindly repeat a potentially completed write. Thesis activation and owner decision writes require separate authorization.

## Materiality model
Revenue/earnings/FCF significance; demand/pricing/margins/competitive evidence; strategic relevance; change versus prior expectation; priced-in expectations; portfolio concentration.

For every surfaced item, expose the relevant dimension and why it could or could not change a decision. Do not apply every dimension mechanically. If the ticker, event facts, or prior thesis are missing, give a provisional decision rule and request only those missing inputs; do not return an intake form without explaining what would make the information material. Keep a no-action/monitor/deeper-review decision distinct from the direction of the evidence, and do not expand triage into full underwriting.

## Output contract
Worth attention now; monitor; no material change; a brief decision-linked materiality reason; direction; provenance; next research question and escalation path; persistence status (`NOT_WRITTEN`, `SAVED`, or `WRITE_FAILED`) and the real canonical WRITE receipt when a write was attempted. With missing facts, include a provisional rule and the minimum required inputs. Keep evidence quality, monitoring execution and persistence as separate fields: unverified evidence may be `PARTIAL_EVIDENCE` while monitoring is `BLOCKED_CANONICAL_READ` and persistence is `NOT_WRITTEN`. Preserve `BLOCKED_THESIS_NOT_ACTIVE` and downstream failures as well; report composition must not replace a blocked execution state with a softer evidence label.

## Stop conditions
Stop when every escalated item has one concrete decision-relevant research question.

## Integrated report presentation
Render the report directly in the chat response by default. External HTML/PDF/Figma/deck/file output is allowed only when the user explicitly requests that artifact or format.

After triage/synthesis, call `report-composer`.

Default profile:
- what requires attention now;
- inline materiality x direction view when useful;
- holding/theme sections with changed evidence;
- event timeline for material changes when useful;
- noise suppressed;
- exact next research questions;
- canonical receipts / limitations, including the exact monitoring execution state.

Keep each visual adjacent to the evidence it summarizes. Do not use price reaction as a visual proxy for thesis validity.
