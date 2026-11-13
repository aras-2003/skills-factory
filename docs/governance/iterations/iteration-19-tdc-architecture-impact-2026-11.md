# Iteration 19 — TDC v1.1 and native Architecture Impact sync (PLANNED)

**PLANNING ONLY.** Follows [iteration delivery](../ITERATION-DELIVERY.md). This is the proposed next increment after iteration 18 reaches CLOSED or ABORTED; do not change iteration 18's frozen #618 scope. Two workstreams are technically independent, but cannot be a second ACTIVE increment.

- State: PLANNED; no lock SHA; no start/close timestamp.
- Tracking Issue: [#688](https://github.com/aras-2003/skills-factory/issues/688).
- Existing implementation candidate: [PR #686](https://github.com/aras-2003/skills-factory/pull/686), Draft; no new implementation PR unless scope/repair demands it.
- Owner / reviewer: Arkadiusz Kamrowski / owner self-review pending optional independent reviewer.
- Baseline main SHA: TO_CONFIRM on activation, not the historical PR base.
- Lock SHA: NOT_SET; assign only after previous iteration terminal and complete acceptance matrix.
- Native Project Iteration field: NOT_SET; Project metadata assignment is independent.
- Dependencies: Iteration 18 terminal; verified Project #1 `Architecture Impact` SingleSelect options and scoped `PROJECTS_TOKEN`.

## Frozen commitment proposal — not yet locked

| Workstream | Acceptance | Included | Excluded | Status |
| --- | --- | --- | --- | --- |
| A: TDC adoption | 19-A1, 19-A2 | Standard v1.1, engineering/bug issue forms, 110 Issue descriptions and source-based sample quality review | Rewriting closed history, changing accepted AC, making all issues Ready | PROPOSED |
| B: Projects field sync | 19-B1..B4 | Existing GraphQL sync reuse, 110-entry versioned manifest, safe dry-run, verified apply, per-Issue exceptions | New project/item creation, overriding reviewed values, auto status/iteration/release changes | PROPOSED |

## 19-A1 — Quality and migration
Evidence from actual Issue bodies for 110 OPEN Issues, with independent spot checks of the specific scope and criteria. Preserve historical text and links; identify residual `TO_CONFIRM` rather than inventing source-derived architecture.

## 19-A2 — Form/standard consistency
Render both Issue Forms and validate `Opis zmiany` as descriptive content while GitHub Project `Architecture Impact` is the canonical A0–A4 classifier. Check no duplicate field and compatibility with governance.

## 19-B1 — Deterministic test gate
Versioned no-network cases for missing/ambiguous Project options and items, changed title, manual conflict, dry-run/no-write, idempotence/readback. Verify required current-main CI and code diff.

## 19-B2 — Live read-only dry-run
Use the standard workflow with `apply=false` to discover configured options, Project item presence, and missing permissions. Record actual run URL + exact manifest SHA, processed/errors. A dry-run does not prove writes.

## 19-B3 — Verified native-field write
After review of proposed impact A0–A4 and actual configured options, run `apply=true`. Each existing Project item is independently read back; record 110 successes or itemized `BLOCKED/NOT_WRITTEN` and remediate without overwriting human decisions. Exact project source/channel identity recorded.

## 19-B4 — Failure and rollback
Document re-run/repair policy, fail-closed behavior, conflicts and manual restoration. No inferred PASS, no automatic status change, no release authority.

## Architecture
Planned impact: A2, reusing `scripts/governance/sync_project_metadata.py` and existing GitHub Projects source of truth. On activation evaluate A3 if verified contract/ownership changes. No new Skill or runtime system.

## Start and close gates
Before activation: verify iteration 18 terminal, freeze issue list/baseline SHA and per-case fixture matrix, confirm owner/reviewer, credential and runtime availability. No parallel ACTIVE.
Before merge: review candidate vs exact current base, complete CI and obtain reviewer authorization.
After merge: verify exact merged main SHA and run `workflow_dispatch` dry-run, then reviewed apply, preserve receipts. Close only with evidence across A1–B4; otherwise BLOCKED/NOT_RUN rather than PASS.
