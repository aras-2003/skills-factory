# Iteration 10 — PRES-03 acceptance matrix

Baseline: `668973da197c8fb7ed9c3840ba884e0d150752a7`. Final main candidate: `ee95deec75a7020007c99cffbc09975d846a51a3` (includes #609 adapter and the subsequent #610 contract-only PR; adapter workflow reran on this exact SHA). Scope remains #609 only plus the explicitly partial #283 parent contribution in the lock record.

| Row | Criterion | Required evidence | Candidate SHA / dependency lock | Runner / tools | Fixture/input hashes | State | Verdict | Output/receipt | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 609-A | Audit/reuse | Source map and reuse boundary | `ee95deec` | repository review + adapter docs | canonical DeckSpec v1 | PASS | PASS | PR #634; `RENDERING.md` documents isolated adapter and non-duplication | owner (self-review) |
| 609-B | Version pin/preflight | CLI/package/browser/LO identity | `ee95deec` | pinned adapter runtime | CI artifact in run #223 | PASS | PASS | Marp adapter workflow #223; exact runtime versions recorded in receipts | owner (self-review) |
| 609-C | Sandbox/security | URL/HTML/path/symlink/timeout/size negative cases | `ee95deec` | adapter security tests | CI artifact in run #223 | PASS | PASS | `Run adapter unit and input security tests` | owner (self-review) |
| 609-D | Real exports/reopen | HTML + PDF + flattened PPTX + experimental editable PPTX generated and reopened | `ee95deec` | Chromium + LibreOffice Impress | CI artifact `sf-presentation-marp-ee95deec…` | PASS | PASS | `Generate, reopen and inspect all output modes`; 4 requested modes | owner (self-review) |
| 609-E | Fidelity/determinism | 16:9, slide count/order, exact data, repeat content hash | `ee95deec` | reopened artifact inspection | CI artifact in run #223 | PASS | PASS | `Generate, reopen and inspect all output modes`; repeat render and source revision checks | owner (self-review) |
| 609-F | Visual/font | per-slide screenshot comparison, drift threshold, fallback receipt | `ee95deec` | Chromium + raster comparison | CI artifact in run #223 | PASS | PASS | Per-slide screenshots, raster comparison and font fallback receipt retained in artifact | owner (self-review) |
| 609-G | PPTX capability | flattened backgrounds/notes; editable objects/notes loss/fidelity recorded | `ee95deec` | LibreOffice Impress + OOXML inspection | CI artifact in run #223 | PASS | PASS | Flattened backgrounds/notes and editable object counts inspected; editable notes limitation recorded | owner (self-review) |
| 609-H | Fail-closed behavior | missing LO/browser and renderer/input errors; no silent downgrade | `ee95deec` | adapter tests + reduced-runtime images | CI artifact in run #223 | PASS | PASS | `Verify missing LibreOffice fails without mode downgrade`; `Verify missing browser blocks browser-backed modes` | owner (self-review) |
| 609-I | Regression | presentation workflows, shared report/visual sentinels and required CI | `ee95deec` | Validate skills, Domain integrity, Site CI, Marp adapter | main runs #1232 / #620 / #223 | PASS | PASS | Exact-main runs: Validate skills #1232, Domain integrity #1232, Site CI #620, Marp adapter #223; all success | owner (self-review) |
| runtime-site | Package/Site/runtime | Isolated adapter is not registered or deployed in this increment | N/A | Site / Cloud Next | N/A | reviewed | N/A | Scope boundary: no Lab/production/Site registration or runtime behavior | owner |

## Inventory

Candidate identity: `ee95deec75a7020007c99cffbc09975d846a51a3`. Main Marp run: [#223](https://github.com/aras-2003/skills-factory/actions/runs/43070251831); artifact ID `13878926304`, SHA-256 `5069ac0764368e60b8d395cb35b52019bc58996ea9a12b7d4dbe5b28985a8db6`, retained until 2027-02-09.

| Layer | Distinct scenarios | Planned runs | PASS | FAIL | NOT_RUN/BLOCKED | Reviewed N/A |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Adapter/security/preflight | 6 | once per candidate | 6 | 0 | 0 | 0 |
| Artifact generation/reopen/fidelity | 4 modes + 3 slide inspections | once per candidate; repeat deterministic render twice | 7 | 0 | 0 | 0 |
| Regression/CI | 4 shared/rotating checks + all required workflows | once per candidate | 4 | 0 | 0 | 0 |
| Site/runtime | 0 | 0 | 0 | 0 | 0 | 1 |

#283 remains open until its complete native Figma/runtime/export acceptance is separately demonstrated. No maturity or production status is inferred.

## Closeout evidence
- Candidate source/final main: `ee95deec75a7020007c99cffbc09975d846a51a3`.
- Main Marp adapter run #223 succeeded on exact SHA. Main Validate skills, Domain integrity, Site CI, Lab packaging and Pages build also succeeded on that SHA.
- The earlier user-supplied ZIP exposed black HTML slide captures from the pre-fix run; PR #634 fixed the hidden parent-SVG selection. The post-merge Marp workflow then passed and retained fresh per-slide screenshots; the older ZIP is not used as acceptance evidence.
- Site/runtime N/A is unchanged: the adapter was not registered or deployed by this scope. #283 remains open.
