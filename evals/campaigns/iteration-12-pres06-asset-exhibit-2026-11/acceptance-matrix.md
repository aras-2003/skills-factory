# Iteration 12 — PRES-06 acceptance matrix

Baseline main: `a8c7159fea9be63f57aa0ddb8c2e1ffed99ac334`. Fixed scope: #612 only. All acceptance rows begin NOT_RUN; scope lock is not implementation or runtime evidence.

| Row ID | Issue / criterion | Layer + case ID / definition | Required / N/A rationale | Candidate SHA + artifact digest | Surface / model / tools | Input / rubric hashes | Execution state | Verdict | Receipt / output / trace + runtime | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 612-A1 | #612 / manifest | Valid asset manifest preserves source ID, license/rights, as-of, alt text, owner and confidentiality | required | pending | adapter unit + receipt test | synthetic fixture + manifest | NOT_RUN | none | pending | owner |
| 612-A2 | #612 / manifest safety | Missing metadata, duplicate IDs, remote/traversal/symlink paths and path escapes fail closed | required | pending | adapter security tests | hostile synthetic inputs | NOT_RUN | none | pending | owner |
| 612-B1 | #612 / architecture diagram | Bounded node/edge graph validates endpoints, renders passive SVG deterministically, and retains separate editable JSON source/hash | required | pending | pinned Marp adapter | synthetic graph + source JSON | NOT_RUN | none | pending | owner |
| 612-C1 | #612 / quantitative chart | Generated SVG uses only referenced finite numeric data and preserves exact value, unit, as-of and provenance | required | pending | adapter + SVG inspection | synthetic numeric fixture | NOT_RUN | none | pending | owner |
| 612-D1 | #612 / table | Visible Markdown table is derived from the same data refs; no independently retyped values; provenance remains inspectable | required | pending | adapter + HTML/PDF text inspection | mixed synthetic fixture | NOT_RUN | none | pending | owner |
| 612-E1 | #612 / SVG and fallback | Passive SVG allowlist, active content rejection, explicit declared local raster fallback for supported mode limits; no fallback for unsafe input or mode substitution | required | pending | adapter security + mode tests | safe, unsafe and fallback synthetic assets | NOT_RUN | none | pending | owner |
| 612-F1 | #612 / mixed deck outputs | One deck with architecture diagram, chart and table renders; receipt matches slide order and values; HTML/PDF/PPTX reopen checks pass within declared image threshold | required | pending | pinned Marp, Chromium, Poppler, LibreOffice | mixed synthetic DeckSpec | NOT_RUN | none | pending | owner |
| 612-G1 | #612 / privacy boundary | Synthetic confidentiality label is preserved; renderer remains network-isolated; remote sources/providers are rejected; no customer data used | required | pending | static/security CI + Docker `--network none` | synthetic sentinel only | NOT_RUN | none | pending | owner |
| 612-H1 | #612 / regression | Adapter unit/security tests, canonical DeckSpec validator, all-mode integration, theme regression, two unchanged-domain probes | required | pending | GitHub Actions PR | locked cases | NOT_RUN | none | pending | owner |
| 612-I1 | #612 / exact main | Final implementation main Validate, Domain, evaluation, Marp and source-bound Site/Pages checks pass; retain artifact identity | required | pending | GitHub Actions | exact main SHA | NOT_RUN | none | pending | owner |
| runtime-site | #612 / Cloud Next runtime | No skill/runtime registration or Cloud Next contract changes in this adapter-only scope; parent #283 acceptance is separate | reviewed N/A | N/A | Cloud Next / Lab | N/A | reviewed | N/A | explicit scope boundary | owner |

Completeness review: all fixed criteria are mapped; each required case has a retained receipt; repeated attempts use unique run IDs; any unsupported renderer/fallback behavior is explicit; no required failure is relaxed or hidden. Parent #283 remains open and cannot be closed by this matrix.

## Inventory and execution totals

| Layer / surface | Required distinct scenarios | Planned executions / repetitions | Executed PASS | Executed FAIL | NOT_RUN / BLOCKED / REVIEW_REQUIRED | Reviewed N/A | Evidence compatibility |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Manifest and local asset safety | 2 | at least once per candidate | 0 | 0 | 2 | 0 | pending |
| Diagram/chart/table semantics | 3 | deterministic repeat for generated assets | 0 | 0 | 3 | 0 | pending |
| Output, fallback, reopen and fidelity | 2 | all four modes; repeated deterministic build | 0 | 0 | 2 | 0 | pending |
| Privacy / network isolation | 1 | once per candidate | 0 | 0 | 1 | 0 | pending |
| Regression and exact-main CI | 2 | PR + exact main | 0 | 0 | 2 | 0 | pending |
| Cloud Next runtime | 0 | 0 | 0 | 0 | 0 | 1 | reviewed N/A |
