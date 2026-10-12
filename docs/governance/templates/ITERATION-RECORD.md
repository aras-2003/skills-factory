# Iteration <id> — <single outcome>

Template only: replace every placeholder before locking. Follow [iteration delivery](../ITERATION-DELIVERY.md).

- State: PLANNED
- Owner / reviewer (state self-review explicitly):
- Tracking Issue / native Project iteration:
- Previous terminal iteration / closure link:
- Baseline main SHA:
- Lock commit SHA (record externally in tracking Issue):
- Started at / closed at (UTC):
- Scope lock reviewed by / at:

## Frozen commitment

| Issue | Outcome / acceptance criterion IDs | Included | Excluded | Dependencies / accepted evidence | Size |
| --- | --- | --- | --- | --- | --- |
| <Issue> | <AC-01> | <bounded scope> | <explicit boundary> | <links> | S/M |

## Test plan

Link completed acceptance matrix. List required surfaces/models/tools, shared sentinel cases, changed dependency paths, campaign definitions, input/rubric hashes and executor/evaluator separation. Record N/A rationale before start. Confirm runtime access and artifact retention plan.

## Candidate history (append; never overwrite)

| Candidate | Main SHA | Lab release ID / payload digest | Build + offline CI | Observed runtime identity / smoke | Supersedes / invalidated rows |
| --- | --- | --- | --- | --- | --- |
| <C1> | <SHA> | <identity> | <run links> | <receipt> | <none or case IDs> |

## Regression selection and counts

- Changed contracts / direct and transitive consumers (evidence links):
- Included cases / exclusions with bounded-impact rationale:
- Fixed sentinels / rotating unchanged-domain probes (minimum 2):
- Last full runtime baseline candidate / behavior iterations since baseline (maximum 4):
- Planned distinct scenarios / executions by layer and required surface:
- Critical stochastic scenarios repeated at least 3 times / instability history:
- PR CI / final-main checks and build / external runtime runs:

## Defect intake and clarifications (append; intake always open)

| Bug Issue / discovery iteration | Existing contract / frozen criterion or unrelated | Severity / closure blocking | Fix PR or accepted deferral owner + future delivery iteration | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |

Report all discovered bugs here, including unrelated/pre-existing failures. Keep discovery attribution when delivery is deferred; record rationale and acceptance. New capabilities use the improvement form and go to a different PLANNED increment. Do not edit the frozen commitment to incorporate them.

## Closure / abort decision

- Outcome: PENDING (CLOSED or ABORTED only after decision)
- Final candidate / matrix and immutable evidence links:
- Committed Issues accepted / unresolved:
- Required rows PASS / FAIL / NOT_RUN / BLOCKED / REVIEW_REQUIRED / reviewed N/A:
- Shared regression verdict:
- Non-blocking findings and accepted impact (owner/reviewer + future Issue):
- Scope compared with lock commit:
- Issue / Project / PR reconciliation:
- Owner proposal / reviewer acceptance / decision timestamp:
- If ABORTED: reason, partial evidence and complete unresolved-criterion mapping:
- Next iteration eligibility (no automatic start or production promotion):
