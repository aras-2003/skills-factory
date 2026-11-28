# A3 architecture review — parallel SDLC Deep work

- Issue: #748, AC-D01..D07
- Exact source: canonical main 642c745a847b56bdf285cae202c68e3e855048d7
- Candidate: NOT_CREATED
- Requested profile: sf-architect, gpt-6.2-sol / high
- Host-observed model, effort, profile: UNKNOWN; collaboration surface does not expose these values.
- Decision: COMPOSE existing Codex roles, pinned App Server controls, exact-revision validation and evidence. Do not create a new orchestrator or Site ACL.

## Work packages and ownership

Four placements are possible, but host capacity remains two active child threads and the existing #748 exception does not raise that limit or the standing WIP policy.

1. Handoff readback and exact-SHA SDLC cycle — one writer for scripts/engineering/delegation_handoff.py, its focused tests, live continuation pins, and the pilot runbook only if contract text changes. This is the only currently proven code task.
2. Native role smoke and usage baseline — evidence-only owner for new #748 role sidecars/receipt. Observe native named role dispatch, distinct tool execution, handoff sizes, and a matched baseline versus compact trial. Record actual usage only when exposed. Do not change model configuration without runtime evidence.
3. App Server tool/filesystem runtime lane — owns the existing MCP ACL canary/fixture and tests only if a real role/thread policy run requires code; otherwise reuse existing canaries. Test actual thread policies and negative I/O; do not claim Desktop inheritance from direct App Server filtering.
4. Permission A/B non-transfer lane — owns approval_nontransfer_canary.py and tests only after a supported scoped auth identity exists or a supported isolated local mock meets preflight. Keep blocked until then; do not weaken security controls.

Tracks 1 and 2 may run concurrently in separate workspaces. Track 3 can inspect/reuse existing bounded evidence, but must not duplicate #829 or expand its claim. Track 4 stays unassigned because its precondition is absent.

## Confirmed source finding

At exact main SHA 642c745a, read_input accepts both bytes and text input of 601 UTF-8 bytes under a declared 600-byte handoff budget when canonical serialization is 463 bytes. Root cause: raw input is checked only against the 16 KiB hard cap while canonical serialization is checked against the declared budget. The absolute cap remains in force. This is a real AC-D04 defect and the recommended first Developer change.

Proposed ownership is limited to scripts/engineering/delegation_handoff.py, tests/test_delegation_handoff.py, and the live compatibility pins in evals/campaigns/iteration-07-investing-quality-2026-11/sdlc-source-compatibility-continuation.yaml plus tests/governance/test_sdlc_architecture_source_example.py.

## Cases and sequence

Freeze raw bytes and text over the declared budget but under the hard cap, exact declared-boundary acceptance, UTF-8 multibyte boundaries, and valid bounded pretty-printed inputs. Test Designer freezes fixtures and expected results before implementation; Developer then works from the exact base; separate Executor and Reviewer bind to the same candidate SHA. Rework only on a real finding, with stale candidate evidence invalidated and selected cases rerun.

## Runtime constraints and recovery

Current exact main has the strict mock-network gate; the latest escalated receipt includes decoy TCP connections. Keep the gate and scope unchanged. Agent role dispatch is observable, but repository TOML loading and effective per-turn effort are not. Agent configuration inherits parent permissions, so per-role tool or filesystem restrictions in TOML are not an enforcement mechanism. Revert only the bounded handoff fix and its live compatibility pins together; preserve historical receipts. No new orchestrator, production action, or broader runtime permission claim is authorized by this design.
