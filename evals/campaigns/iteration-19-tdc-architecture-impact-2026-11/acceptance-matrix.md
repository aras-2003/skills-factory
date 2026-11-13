# Iteration 19 — TDC v1.1 acceptance matrix

Candidate baseline main: `22d31320e6114d8c1dbe6b1ed79dff12cb2223cf`; final source SHA and versioned manifest hash to be recorded after integration. Scope locked by the companion Iteration 19 record. `NOT_RUN` is not `PASS`.

| Case | Issue | Required observable result | Input / test fixture | Expected evidence | Status |
| --- | --- | --- | --- | --- | --- |
| 19-A1 | #688 | 110/110 captured Issues contain specific descriptions, preserved original AC and reasoned architecture impact; sampled semantic quality reported separately | Original 110 issue identifiers, live GitHub readback + coverage script/manual sample | Before/after source Issue URLs, counted manifest and sample notes | NOT_RUN |
| 19-A2 | #688 | Markdown TDC standard and engineering/bug Issue Forms are valid and show only descriptive `Opis zmiany`, not duplicate Project classifier | PR source files and GitHub Issue Forms | Parsed YAML, verified source and UI rendering notes | NOT_RUN |
| 19-B1 | #688 | Manifest schema/test suite, authorization fail-closed and exact PR + main CI | `tests/governance/test_task_architecture_sync.py`, existing project sync tests | Source SHA and passing deterministic test/CI URLs | NOT_RUN |
| 19-B2 | #688 | All selected existing Project items and configured field/options discoverable without writing | GitHub Actions workflow_dispatch apply=false, issue_number=0 | Run ID/URL, GH project metadata, processed/failed counts | NOT_RUN |
| 19-B3 | #688 | Actual native `Architecture Impact` values written and independently reread or itemized BLOCKED | GitHub Actions workflow_dispatch apply=true, issue_number=0 after review | Run ID/URL, case list with verified readback and exceptions | NOT_RUN |
| 19-B4 | #688 | Missing project item/options/title drift/conflict never silently overwrite or report PASS | Negative fixture + live error responses | Test receipts, rollback/repair guide | NOT_RUN |
| 19-R1 | #688 | Existing priority/status/iteration synchronization and adjacent governance unaffected | Current `test_project_metadata_sync.py`, domain-integrity and validate-skills runs | Exact source SHA and regression run links | NOT_RUN |

Review: owner self-review only. No production plugin work or Site runtime acceptance is part of this governance task.
