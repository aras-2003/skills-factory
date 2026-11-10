# Iteration 10 — PRES-03 acceptance matrix

Baseline: 668973da197c8fb7ed9c3840ba884e0d150752a7. Scope is #609 only plus the explicitly partial #283 parent contribution described in the lock record. No implementation has started.

| Row | Criterion | Required evidence | Candidate SHA / dependency lock | Runner / tools | Fixture/input hashes | State | Verdict | Output/receipt | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 609-A | Audit/reuse | Sources and ownership map | pending | repository review | n/a | NOT_RUN | pending | pending | owner |
| 609-B | Version pin/preflight | CLI/package/browser/LO identity | pending | isolated adapter runtime | pending | NOT_RUN | pending | pending | owner |
| 609-C | Sandbox/security | URL/HTML/path/symlink/timeout/size negative cases | pending | adapter security tests | pending | NOT_RUN | pending | pending | owner |
| 609-D | Real exports/reopen | HTML + PDF + flattened PPTX + experimental editable PPTX generated and reopened | pending | compatible CI runner, Chromium, LibreOffice Impress | pending | NOT_RUN | pending | pending | owner |
| 609-E | Fidelity/determinism | 16:9, slide count/order, exact data, repeat content hash | pending | artifact inspection | pending | NOT_RUN | pending | pending | owner |
| 609-F | Visual/font | per-slide screenshot comparison, drift threshold, fallback receipt | pending | Chromium + raster comparison | pending | NOT_RUN | pending | pending | owner |
| 609-G | PPTX capability | flattened backgrounds/notes; editable objects/notes loss/fidelity recorded | pending | LibreOffice Impress + PPTX inspection | pending | NOT_RUN | pending | pending | owner |
| 609-H | Fail-closed behavior | missing LO/browser and renderer/input errors; no silent downgrade | pending | adapter tests | pending | NOT_RUN | pending | pending | owner |
| 609-I | Regression | presentation workflows, shared report/visual sentinels and required PR CI | pending | repository CI | existing locked probes | NOT_RUN | pending | pending | owner |
| runtime-site | Package/Site/runtime | Isolated adapter is not registered or deployed in this increment | N/A | Site / Cloud Next | N/A | reviewed | N/A | Scope boundary: no Lab/production/Site registration or runtime behavior | owner |

## Inventory

| Layer | Distinct scenarios | Planned runs | PASS | FAIL | NOT_RUN/BLOCKED | Reviewed N/A |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Adapter/security/preflight | 6 | once per candidate | 0 | 0 | 6 | 0 |
| Artifact generation/reopen/fidelity | 4 modes + 3 slide inspections | once per candidate; repeat deterministic render twice | 0 | 0 | 7 | 0 |
| Regression/CI | 4 shared/rotating checks + all required workflows | once per candidate | 0 | 0 | 4 | 0 |
| Site/runtime | 0 | 0 | 0 | 0 | 0 | 1 |

#283 remains open until its complete native Figma/runtime/export acceptance is separately demonstrated. No maturity or production status is inferred.
