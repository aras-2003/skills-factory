# Iteration 19 — TDC v1.1 and Projects Architecture Impact sync

- **State: CLOSED / ACCEPTED** as of 2026-11-14. Evidence and explicit #618 blocked result: [closeout evidence](../../../evals/campaigns/iteration-19-tdc-architecture-impact-2026-11/closeout-evidence.md). Iteration 18 was CLOSED / ACCEPTED before this scope began via [PR #690](https://github.com/aras-2003/skills-factory/pull/690); #618 is closed and was not rewritten.
- Tracking Issue: [#688](https://github.com/aras-2003/skills-factory/issues/688).
- Owner / reviewer: Arkadiusz Kamrowski / owner-delegated Codex review; not independent.
- Baseline main SHA: `22d31320e6114d8c1dbe6b1ed79dff12cb2223cf`.
- Scope lock SHA: `5fdd175` (PR #691).
- Started: scope-lock merge `5fdd175`; closed: 2026-11-14 after required evidence was integrated in PR #696 and apply run #43594714254 was itemized.
- Native GitHub Project iteration: NOT_ASSIGNED (scheduling mirror, not authorization).
- Source candidate: stale PR #686 was closed; its unsafe/out-of-scope diff was replaced by clean PR #693 and follow-up PR #694. PR #695 records the reviewed manifest and audit; PR #696 records final evidence.
- Governance: [ITERATION-DELIVERY](../ITERATION-DELIVERY.md); one active increment, max 2 implementation WIP + 1 validation lane.

## Frozen scope

| Workstream | Locked outcome | Included | Excluded | Size |
| --- | --- | --- | --- | --- |
| A — issue definition | TDC 19-A1/A2: source-controlled task definition standard, engineer/bug Issue Forms, and verified 110 frozen Issue descriptions with exact captured acceptance-summary preservation; owner-delegated review only, no independent quality certification | Docs, issue forms, read-only/safe inspection of 110 issue bodies and representative quality spot checks; no claims of universal Ready | Rewriting historic closed issues, altering scope of other locked iterations, automatic Ready or release | S |
| B — Project custom field | TDC 19-B1..B4: Project V2 `Architecture Impact` A0–A4 synched from versioned 110-entry manifest via existing Projects token/GraphQL, readback verified | Existing `PROJECTS_TOKEN` + `scripts/governance/sync_project_metadata.py`; new bounded safe sync, manifest/tests, manually dispatched dry-run and reviewed apply | New Project, silently creating items/options, overwriting human decisions, status/iteration writes, production runtime/deployment, moving old Issues to Ready | M |

## Architecture design / affected contracts

- **Proposed impact A2** — compatible extension of existing Project metadata governance mechanism. Re-evaluate as A3 if actual GraphQL Project item, authoring, or ownership boundaries differ.
- **Current source:** `scripts/governance/sync_project_metadata.py`, `.github/workflows/maintenance-project-metadata.yml` and existing `PROJECTS_TOKEN`; canonical native GitHub Project #1 remains source of truth for `Architecture Impact` classification.
- **Target delta:** versioned, issue-specific input manifest and a separately dispatchable workflow with clear `apply=false` default, exact ProjectV2 field/option matching, conflict/no-overwrite policy, after-write readback.
- **Unchanged:** existing Project metadata sync and fields (Priority/Size/Area/Status/Iteration), SKILL.md, runtime/production, skill routing, and source of content for existing Issue history.
- **Dependency:** new workflow file must reach `main` before manual dispatch; confirm installed Project field options/permissions in live dry-run. Proposed A0–A4 assessments are not retroactively approved architecture decisions.

## Locked acceptance criteria and cases

Use [the acceptance matrix](../../../evals/campaigns/iteration-19-tdc-architecture-impact-2026-11/acceptance-matrix.md), case IDs `19-A1`, `19-A2`, `19-B1` through `19-B4` and `19-R1`. No relaxation after this commit.

1. **19-A1 (issue coverage):** query all open Issues at freeze, reconcile exactly the 110 initial inputs by number and source; 110/110 have specific `Opis zmiany`, expected criteria and architecture scope, without losing old requirements. Newly opened issues after baseline are a separate change delta, not silent denominator drift. Manual spot check representative EPIC/DESIGN/IMPLEMENT/DISCOVERY and high-impact A3 issues; actual quality verdict distinct from format presence.
2. **19-A2 (forms):** source-controlled TDC v1.1 and engineering/bug forms are parsable, human-readable, and do not duplicate native Projects custom-field classifier; exact PR and merged-main verification.
3. **19-B1 (offline):** deterministic no-network tests cover manifest schema, exact field/option match, missing membership, title drift, safe dry-run, conflict refusal, idempotent same-value behavior and post-write readback. Required PR CI and exact-main checks.
4. **19-B2 (live dry-run):** `workflow_dispatch(apply=false, issue_number=0)` on main, confirm real Project #1, field name/options A0–A4, Project membership and credential. Record run URL, source SHA, total processed and all failures; dry-run is **not** proof of a write.
5. **19-B3 (live apply):** only after impact assessment review. `workflow_dispatch(apply=true, issue_number=0)`, capture per-item mutation plus independent readback and end count. Each 110 expected Issue either VERIFIED/ALREADY_VERIFIED or explicitly blocked with reason; no false blanket success. If manifest proposes impact that cannot be substantiated, postpone that item, don't forge approval.
6. **19-B4 (safety/recovery):** show negative cases for missing fields/options/item/title conflicts, no overwrite of differing human value, error reporting, rollback/restore policy; no status, iteration, release, source skills or other Project fields changed.
7. **19-R1 (regression):** prior project-metadata sync tests and shared governance/validation CI pass; no change to existing metadata field semantics; full PR-head, merged-main and run identities kept distinct.

## Execution sequence and evidence

- Scope lock first; then review PR #686 complete diff against actual main, confirm behavior fits this locked contract and capture current CI. Preserve the issue description updates already live as baseline evidence; do not claim they were created by this integration.
- Merge candidate only after the required source CI, review and merge authorization. Exact merged main checks and markdown/form verification are separate from PR-head PASS.
- Execute a **live read-only dry-run** before allowing mutation; manual `apply=true` only after review of suggested impact levels and configured project options. Do not suppress errors.
- Evidence to retain: main/PR SHA, run URLs, complete 110-entry manifest SHA, per-Issue outcome log, failing item reasons and owner review. Inability to dispatch a workflow through the Chat GitHub connector is a tooling blocker, not evidence of a successful run.

## Closure

Close only if all required rows PASS with exact-version evidence; otherwise stay VALIDATING/BLOCKED. Offline CI never substitutes live Project field readback. Runtime/Site MCP is N/A for this governance-only automation with rationale recorded at scope lock; **GitHub Actions Project read/write** is required for B2/B3. Owner review is delegated Codex review; independent reviewer acceptance is not implied.


## Closure evidence and decision

See `evals/campaigns/iteration-19-tdc-architecture-impact-2026-11/closeout-evidence.md` for the exact PR/main/run identities, 109 verified Project values, blocked closed Issue #618, scope reconciliation, limitations and owner decision. No Site/plugin release or runtime promotion was performed. The explicit #618 refusal is the required fail-closed behavior and is not represented as a write or successful readback.
