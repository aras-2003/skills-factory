# P0 evidence reconciliation — 2026-10-09

This is a **bounded implementation and reconciliation entrypoint**, not a claim that
14 historical P0 items are finished. The legacy `BACKLOG.json` is historical
and its statuses are not current GitHub Issue/Project state.

## Verified directly from main

- `.github/workflows/validate-skills.yml` already runs security scanner,
  capability contract validator, static routing collision report, isolation
  tests, release/readiness tests and packaged artifact validation.
- `workflows/skill-development/WORKFLOW.md` already classifies
  NEW/ROUTING/BEHAVIOR/RESOURCE/DOCS changes.
- `skills/meta/skill-release-review/SKILL.md` already requires exact
  source/build/package/manifest identity and forbids conflating approval
  recommendations with deployment.
- `release/production-readiness.yaml` uses pending receipt states and
  personal-beta owner/expiry fields.

These are **source observations**, not claims of runtime/browser PASS,
configured GitHub rulesets, or completed historical acceptance criteria.

## Auditable inventory

Run:

```bash
python scripts/roadmap/audit_p0.py --output .tmp/p0-audit.json
python -m unittest discover -s scripts/roadmap/tests -p 'test_*.py'
```

The tool checks historical P0 IDs, duplicate IDs, missing/self dependencies,
and cycles through non-P0 dependencies. Every task is marked
`evidence_state: UNVERIFIED` until a separately reviewed source revision,
PR, CI receipt and runtime receipt justify a more specific disposition.

## Disposition and ordering

1. ENG-01/02 — reconcile exact source and release policy.
2. ENG-15/16/20 — verify scanner, side-effects, protections, publisher.
3. ENG-03/04/05/06/10 — validate meta skill behavior and routing.
4. ENG-08/17 — evaluate runner and registry gaps.
5. E2E-01/02 — verify exact deployed runtime + UI/browser receipts.

Open review-required Issues must not be closed because this report exists.
Do not modify E2E baseline, queue, receipts or claim a deployed Site.

## Verified source snapshot and outstanding P0 evidence

This reconciliation was inspected against `main` SHA
`a66f7cf40adbbfce31248c6f806016a4f27e93cb`, **not** the historical
`ai-skills` repository identifier embedded in BACKLOG.json.

- Source inventory from recursive GitHub tree: **54** `skills/**/SKILL.md`,
  **17** `workflows/*/WORKFLOW.md`.
- Checked-in `docs/lab-release.json`: Lab **0.33.5**, source
  `99e41a56993b198a36be07ab8c247db1aa33c575`, **70** components
  (54 skills + 16 workflow entrypoints). Lab identity is **not** current
  main identity and does not prove the current Site deployment.
- `release/capability-contract.yaml` has an empty
  `component_declarations` map: **70/70 UNASSESSED** in the source
  validator. This is a material residual ENG-16/17 gate.
- GitHub rulesets readback returned an empty list. Branch protection
  reads for main and production returned HTTP 403 (integration lacks
  permission); do **not** infer protected or unprotected state.
- `.github/workflows/package-main-lab-plugin.yml` creates artifacts with
  read-only repository permissions. This is not the missing separately
  authorized deployment publisher.

### Per-P0 evidence-bound disposition (not closures)

| ID | Observed implementation evidence | Residual / gating evidence |
|---|---|---|
| ENG-01 | Source tree + Lab manifest counts confirmed above | Historical AIS/RT item-by-item reconciliation not verified |
| ENG-02 | Lifecycle, release review and readiness include pending evidence/personal-beta gates | Exact-version policy scenario tests and full reconciliation |
| ENG-03 | `skill-test-design` draft + eval fixtures exist | Independent runtime evidence for candidate maturity |
| ENG-04 | `skill-evaluation`, isolation tools and receipts exist | Baseline/previous-version comparable live evidence |
| ENG-05 | `skill-release-review` and isolated campaign exist | Positive/missing/high failure runtime decisions |
| ENG-06 | Existing `skill-development` change classification and scoped testing | End-to-end handoff/early test design evidence |
| ENG-08 | `scripts/eval/receipt.py` and `campaign.py` exist | Controller-only one-command, idempotent CLI/Desktop receipts |
| ENG-10 | Static collision report and routing tests in CI | Natural model routing and margin evidence |
| ENG-15 | Runtime/skill security scanner and mutation tests in CI | Confirm comprehensive packaged runtime scanner coverage |
| ENG-16 | Capability dimensions schema and report exist | 70 unassessed component declarations; no compatibility PASS |
| ENG-17 | Generated catalog and package manifest exist | Registry/contract assessment parity and current channel identity |
| ENG-20 | SHA refs + hashed dev lock; immutable action-ref CI guard in this PR | Admin ruleset/protection verification, publisher isolation/rollback |
| E2E-01 | Read-only `runtime_info` in MCP source and tests | Exact deployed Lab/Site identity and stale-registration proof |
| E2E-02 | Runtime E2E fixtures, receipts and historical tests | Browser/UI chart visibility, full tool trace and exact-version closures |

**No P0 row above is marked DONE.** Outstanding runtime and GitHub-admin
requirements cannot be inferred from source files, PR metadata, or this audit.

## GitHub Issues execution status — 2026-10-09

The **14 historical P0 IDs** have been individually updated in the matching
GitHub Issue bodies, preserving original scope, dependencies and the P0
priority. This document does not overwrite immutable historical backlog source
or treat completion as inferred from CI.

| Status | Issues | Count |
|---|---|---:|
| IN_PROGRESS | [ENG-01 #234](https://github.com/aras-2003/skills-factory/issues/234), [ENG-02 #235](https://github.com/aras-2003/skills-factory/issues/235), [ENG-06 #239](https://github.com/aras-2003/skills-factory/issues/239), [ENG-08 #240](https://github.com/aras-2003/skills-factory/issues/240), [ENG-10 #241](https://github.com/aras-2003/skills-factory/issues/241), [ENG-15 #245](https://github.com/aras-2003/skills-factory/issues/245), [ENG-17 #247](https://github.com/aras-2003/skills-factory/issues/247), [E2E-01 #250](https://github.com/aras-2003/skills-factory/issues/250) | 8 |
| BLOCKED | [ENG-03 #236](https://github.com/aras-2003/skills-factory/issues/236), [ENG-04 #237](https://github.com/aras-2003/skills-factory/issues/237), [ENG-05 #238](https://github.com/aras-2003/skills-factory/issues/238), [ENG-16 #246](https://github.com/aras-2003/skills-factory/issues/246), [ENG-20 #248](https://github.com/aras-2003/skills-factory/issues/248), [E2E-02 #251](https://github.com/aras-2003/skills-factory/issues/251) | 6 |
| DONE | None — no end-to-end acceptance claim | 0 |

`BLOCKED` here means at least one essential evidence/environment/control
precondition for closure is absent, **not** that source work cannot be done.
GitHub Project board custom Status fields were not changed by these Issue
body updates; use Issue descriptions as the verified execution disposition
until the connected Project field can be updated and read back.

CI evidence for commit `ae1d7e3286e7e2a446763b1d54debc51c4c2055c`:
- [Validate Skills PASS](https://github.com/aras-2003/skills-factory/actions/runs/37975442668)
- [Domain Integrity PASS](https://github.com/aras-2003/skills-factory/actions/runs/37975442644)

Neither workflow is proof of external browser display, GitHub branch
protection, or skill runtime-model candidate promotion.
