# SDLC Deep implementation plan

## Source and authorization

- Base: canonical `origin/main` commit `538d800534cf7f7eca32640592a90d252f6dbada`; candidate branch begins from the exact canonical tree.
- Owner authorized a one-time exception to D2 on 2026-11-27 so this SDLC package can start while existing Project WIP is 2/2. Exception scope is one package only; it does not raise the ongoing cap or authorize parallel SDLC packages.
- Active package: #748 role-decision routing observability and bounded handoff, because it is the prerequisite for the other Deep items. #766 remains closed under explicit owner risk acceptance. #765, #767–#769 remain unstarted until dependency/capacity allows; existing closed states are not acceptance evidence.
- Maximum child concurrency remains two. One writer per shared interface. The current test design and Architect advisory were completed on the same main tree and are carried forward as evidence.

## Architecture decision

**EXTEND** the current role-decision record contract. Add explicit structured routing trigger data in a new compatible schema version; preserve all v1.0/v1.1 readers and acceptance/rejection behavior. Separate routing appropriateness from dispatch chronology. A1 qualifying shared-contract/trust-boundary invocations may be on time; A2 skips without material trigger may be correct. `UNKNOWN` trigger never proves routing correctness. Roll back by stopping new-version writes while retaining a compatible reader.

The source-linked Architect advisory and 9-case Test Designer plan are in `architect-review.md` and `test-design-and-baseline.md`. The discovered baseline false rejections are captured there.

## Bounded candidate scope

Primary behavioral change:

- `scripts/eval/schemas/role-decision-record.schema.json`
- `scripts/eval/role_decision_record.py`
- `scripts/eval/tests/test_role_decision_record.py`
- `docs/governance/CODEX-ROLE-OBSERVABILITY.md`
- applicable role-decision records only if the version migration requires it; never rewrite frozen historical evidence.

Potential consumers to verify before edit: role-decision validator CLI and directory scan, CI validation job, documentation/eval README, all historical sidecars, and existing retry-chain checks.

## Test-first map

| Case | Baseline behavior / acceptance |
| --- | --- |
| ROUTE-TRIGGER-01 | A1 + qualifying shared-public-contract/trust-boundary + natural INVOKE + accepted dispatch before action accepts `ON_TIME`; baseline currently rejects. |
| ROUTE-TRIGGER-02 | A2 + explicit NONE + SKIP may accept `CORRECT_SKIP`; qualifying A2 trigger + INVOKE is positive; timing still needs chronology. |
| ROUTE-TRIGGER-03 | Qualifying A1/A2 SKIP followed by a proven dependent action accepts `MISSED`; A3/A4 `CORRECT_SKIP` remains invalid. |
| ROUTE-TRIGGER-04 | Natural unnecessary invocation retains reviewer-rationale rule; USER_REQUEST remains separate. |
| ROUTE-TRIGGER-05 | Missing, invalid or contradictory trigger fails closed; UNKNOWN cannot prove routing correctness. |
| ROUTE-TRIGGER-06 | Exact timestamps/bounds, dispatch acceptance and event chronology remain enforced. |
| ROUTE-TRIGGER-07 | Retry structural fields remain immutable; a new signal creates a linked decision. |
| ROUTE-TRIGGER-08 | v1.0/v1.1 results remain unchanged; v1.2 must not fall through a v1.0 code path. |
| ROUTE-TRIGGER-09 | CLI validates every historical sidecar and retry chain without modifying frozen records. |

The pre-change evidence is 13/13 role-decision tests passing on exact main, plus the two synthetic RED reproductions described in `test-design-and-baseline.md`.

## Delivery and closeout

1. Implement this package with one Developer writer and exact base/candidate identity.
2. Run the focused red/green regressions, all historical sidecars through the CLI, then relevant role/handoff/crosswalk and repository suites.
3. Have a separate Test Executor run the exact candidate without edits; have a separate Independent Reviewer review the full diff and evidence.
4. Run available live MCP checks and record receipts separately. Mark unsupported Codex host ACL/profile/restart/cost cases BLOCKED or UNKNOWN with a specific capability and resumption condition; never claim runtime PASS from config/CI.
5. Reconcile each existing Issue acceptance criterion and Project state. Reopen any `not_planned` issue only when its work is actually resumed; do not mark incomplete runtime or production authorization as Done.
6. After #748, use remaining capacity sequentially for #765 and #767, then campaign #768 and coverage refresh #769. #769 frequency remains unknown without a real observation denominator.
7. No Site publication/production deployment occurs without its own verified source bundle and explicit release gate.

## Implementation run — 2026-11-27

- Code candidate tree: `42cd9a80752eca326e23ac18350364fd8d793d9b`, based on exact main `538d800534cf7f7eca32640592a90d252f6dbada`. The candidate changes exactly the five bounded files listed above; no historical v1.0/v1.1 sidecars were rewritten.
- Developer's meaningful RED/GREEN and root-cause notes are documented in the handoff: the validator previously conflated trigger suitability with timing, allowed UNKNOWN to establish a correct skip, and accepted trigger classes inconsistent with impact. Rework added fail-closed cases for those contradictions.
- Independent Test Executor on the exact staged candidate: focused role-decision suite **25/25 PASS**; role/architecture/E2E/handoff regressions **44/44 PASS**; historical CLI validation **10 records**; all diff checks exit 0. Executor made no changes. Requested/effective host model and effort were not exposed.
- Independent Reviewer on the same staged candidate: **no material findings** after three review iterations. It verified trigger/impact consistency, UNKNOWN/CORRECT_SKIP rejection, NONE/MISSED rejection for natural skips, qualifying invoke/UNNECESSARY rejection, USER_REQUEST handling and legacy compatibility. Reviewer made no changes; effective host model/effort/profile remain UNKNOWN.
- `change_gate.py` returned `PLAN_READY` for A3; its report explicitly leaves runtime `NOT_RUN`, `runtime_pass_claim=false`, release unauthorized, dependency graph UNKNOWN.
- Actual Codex role dispatch occurred for Architect and Developer during this task, but selected TOML profile and effective reasoning effort were not observable. Host permission denial, restart/resume, permission non-transfer, primary-session profile load and token/tool savings remain UNKNOWN or NOT_RUN. No runtime or security PASS is inferred from the local tests.
- Candidate code-tree tests and review are complete; commit/CI and remaining #748 host-specific acceptance are separate gates.
