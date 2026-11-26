# SDLC Deep test design and baseline evidence

Source revision: `538d800534cf7f7eca32640592a90d252f6dbada` (`origin/main`). This document captures test design and a read-only exact-main baseline; it is not a candidate implementation or runtime acceptance.

## Test Designer role observation

Requested `sf-test-designer` / `gpt-6.1-terra` / medium. Host-observed model: `gpt-6.1-terra`. Effective effort and named profile: UNKNOWN; host did not expose them. No source edits or test execution were performed by the Test Designer.

## Proposed routing-trigger cases (`ROUTE-TRIGGER-01..09`)

1. A1 + shared-public-contract/trust-boundary + natural INVOKE, accepted dispatch before dependent action: `ON_TIME` chronology should validate; current baseline incorrectly rejects it.
2. A2 + explicit NONE trigger + SKIP: independent `CORRECT_SKIP` should validate; a qualifying A2 trigger plus INVOKE is a positive case. `ON_TIME` without chronology evidence must fail.
3. A1/A2 qualifying trigger + SKIP + later dependent action: `MISSED` should remain recordable. A3/A4 `CORRECT_SKIP` remains invalid.
4. A0/A1 NONE + INVOKE requires `UNNECESSARY` with reviewer rationale or `UNKNOWN`. A2 NONE + INVOKE follows the same principle. `USER_REQUEST` remains distinct.
5. Missing, empty, invalid-enum or contradictory trigger evidence fails closed. UNKNOWN trigger does not prove routing correctness. Timing and routing correctness remain separate.
6. Preserve bounds, accepted-dispatch, and reviewer chronology rules; do not fabricate timestamps.
7. Retry cannot change structural trigger, impact, decision, or signals; a genuinely new signal creates a linked decision.
8. Frozen v1.0/v1.1 acceptance and rejection behavior remains unchanged. v1.2 chronology must not fall through the current exact-v1.1 branch into v1.0 logic.
9. Validate all historical sidecars through the CLI (including retry-chain checks) and preserve their hashes and outcomes.

## Exact-main baseline

- A clean `git archive` snapshot of exact `origin/main` was extracted to `/private/tmp/sdlcdeep-base-su7qh14r`.
- `python -m unittest -v test_role_decision_record` using `/private/tmp/sf-publish-20261123-venv/bin/python` in the clean snapshot's `scripts/eval/tests`: **13/13 PASS**, exit 0.
- Synthetic RED reproductions against that same exact-main validator:
  - A1 natural INVOKE / ON_TIME was rejected with `NATURAL A0/A1 INVOKE requires UNKNOWN or UNNECESSARY assessment with reviewer rationale`.
  - A2 SKIP / CORRECT_SKIP was rejected with `CORRECT_SKIP is inconsistent with impact A2-A4` and `SKIP for impact A2-A4 requires MISSED or UNKNOWN timing assessment`.
- These RED cases are constructed fixtures, not real-host runs. The green baseline proves current tests pass while missing these policy cases; it does not prove runtime behavior.

## Additional repository verification on current main tree

Executed after the live MCP check using `/private/tmp/sf-publish-20261123-venv/bin/python` against checkout `c19ecf960649049f2c9ae08828498b00c2918975`; its Git tree is identical to `origin/main` `538d800534cf7f7eca32640592a90d252f6dbada` (`fd964e73c83f13515ea7b6209802871742b62816`). All commands exited 0:

| Command suite | Result |
| --- | ---: |
| `tests.test_codex_agent_team tests.governance.test_sdlc_deep_role_architecture tests.governance.test_sdlc_deep_e2e_campaign` | 15/15 PASS |
| `tests.test_delegation_handoff` | 29/29 PASS |
| `test_iteration02_semantic_coverage` | 44/44 PASS |
| `test_role_decision_record` | 13/13 PASS |

These source tests verify the declarations, deterministic contracts, generated inventory behavior, and validator baseline. They do not execute the campaign's real-host E2E scenarios, demonstrate technical permission denials, or disprove the two synthetic validator defects above.

## Runtime and backlog status

- Live MCP verification completed read-only on 2026-11-26: `runtime_info` reports Site attestation `verified`, canonical GitHub main/source revision `538d800534cf7f7eca32640592a90d252f6dbada`, deployed Lab release `1.38.607`, 98 catalog entries (79 skills + 19 workflows), and ten advertised capabilities: `runtime_info`, `list_skills`, `load_skill`, `route_investment_request`, `evaluate_investment_decision_fixture`, `calculate_opportunity_scores`, `compare_peer_comparability`, `calculate_issuer_exposure`, `render_bar_chart`, `render_line_chart`.
- Real tool calls returned `SUCCESS` receipts for `runtime_info`, `list_skills`, and `load_skill(skill-development)` pinned to canonical revision `538d8005…`. `load_skill` returned the packaged workflow and its declared required dependency list. Receipts are explicitly unsigned and do not prove that a scheduled task can invoke MCP tools.
- `skill-development` is registered for Lab, maturity `draft`; the other two channels report unavailable. `runtime_info` declares `execution_mode: host_model_executes_loaded_instructions`, so the MCP serves instructions and the host model performs the reasoning. This call did not execute the complete workflow, specialist roles, repository changes, or its gates.
- Campaign `evals/campaigns/sdlc-deep-e2e-2026-11/campaign.yaml`: `E2E-01..05` and `G0..G10` all remain `NOT_RUN`.
- GitHub Project development WIP observed at `2/2`: #619 In review and #754 In progress. Other active items #674/#677/#683 are explicitly blocked and excluded. D2 does not allow starting another package until capacity changes.
- The crosswalk generator was rerun after temporarily moving the untracked audit sidecars outside the checkout. The clean impact queries returned `QUERY_COMPLETE` for `workflow:investment-os-review`, `workflow:oaf-enterprise-architecture-review`, and `workflow:skill-development`; unresolved edges were empty in all three. The full generated matrix contained 98 components, SHA-256 `b701fd3c20d78dd37c0f9ab414656b0442a7ea681c08028ff2dd51dfc313895a`, pinned by the current checkout commit `c19ecf960649049f2c9ae08828498b00c2918975`. This checkout tree is identical to `origin/main` tree; the commit IDs differ. Temporary JSON query outputs are under `/private/tmp/affected-*.json` and the full crosswalk is `/private/tmp/sdlcdeep-crosswalk-20261126.json`.
- This file began as a read-only exact-main baseline. Follow-on implementation and candidate results are recorded in `implementation-plan.md`; this historical baseline remains unchanged as evidence of pre-fix behavior.
