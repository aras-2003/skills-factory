# Iteration 19 — TDC v1.1 acceptance matrix

Locked baseline main: `22d31320e6114d8c1dbe6b1ed79dff12cb2223cf`; final evidence source main: `356c2c0733611b4a4de30d3f57fc82305bfadb96`; manifest SHA-256: `edf1ccc4a526aee511ee6f747375cccceaab289f482be10f273fec66ddb1f1ab`. Scope is locked by the companion Iteration 19 record. `NOT_RUN` is not `PASS`.

| Case | Issue | Required observable result | Input / test fixture | Expected evidence | Status |
| --- | --- | --- | --- | --- | --- |
| 19-A1 | #688 | 110/110 captured Issues contain specific descriptions, preserved original AC and reasoned architecture impact; sampled semantic quality reported separately | Original 110 issue identifiers, live GitHub readback + coverage script/manual sample | 110/110 exact frozen acceptance-summary substring matches and title matches; 7 quality spot-checks and limitations in audit | PASS |
| 19-A2 | #688 | Markdown TDC standard and engineering/bug Issue Forms are valid and show only descriptive `Opis zmiany`, not duplicate Project classifier | PR source files and GitHub Issue Forms | PR #695 CI; live GitHub UI render of both forms; no Issue submitted; audit details | PASS |
| 19-B1 | #688 | Manifest schema/test suite, authorization fail-closed and exact PR + main CI | `tests/governance/test_task_architecture_sync.py`, existing project sync tests | 19 metadata + 18 sync unit tests; PR #695 all CI; main SHA `356c2c0` checks in run #43594693129 and #43594693187 | PASS |
| 19-B2 | #688 | All selected existing Project items and configured field/options discoverable without writing | GitHub Actions workflow_dispatch apply=false, issue_number=0 | Run #43593376206 on `6ddd15e`; 110 processed, 0 errors; field single-select A0–A4 plus unused extra `Epic`; no writes | PASS |
| 19-B3 | #688 | Actual native `Architecture Impact` values written and independently reread or itemized BLOCKED | GitHub Actions workflow_dispatch apply=true, issue_number=0 after review | Run #43594714254 on exact main `356c2c0`; 109 VERIFIED/readback; #618 BLOCKED because closed; 110 processed, 1 explicit refusal; complete IDs in closeout-evidence.md | PASS WITH EXPLICIT BLOCK |
| 19-B4 | #688 | Missing project item/options/title drift/conflict never silently overwrite or report PASS | Negative fixture + live error responses | Unit tests cover missing membership/options, title drift, differing manual values, readback mismatch, closed Issue refusal; live #618 refusal; recovery steps in standard | PASS |
| 19-R1 | #688 | Existing priority/status/iteration synchronization and adjacent governance unaffected | Current `test_project_metadata_sync.py`, domain-integrity and validate-skills runs | 19 metadata tests; merged-main validate/domain and full CI jobs all green on `356c2c0` | PASS |

Review: owner-delegated Codex review of planned impact only; not independent. No production plugin work or Site runtime acceptance is part of this governance task.
