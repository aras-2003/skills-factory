# Iteration 11 — PRES-05 acceptance matrix

Baseline: `2ebd353277c5c2551ca345ee89cc9fab711c3d41`. Scope is #611 only. All rows begin NOT_RUN; this lock is not an implementation or runtime PASS.

| Row | Criterion | Required evidence | Candidate SHA / dependency lock | Runner / tools | Fixture/input hashes | State | Verdict | Output / receipt | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 611-A | Registry | 4+ original styles + editable-safe variant; valid IDs/versions/token metadata | pending | registry validator | registry + synthetic gallery | NOT_RUN | pending | pending | owner |
| 611-B | Layout grammar | 6+ semantic layouts; aliases and invalid layout rejection | pending | adapter unit tests | gallery DeckSpec | NOT_RUN | pending | pending | owner |
| 611-C | Readability/license | >=4.5:1 text contrast; exact package license/attribution/fallback; no copied templates | pending | contrast/license tests + source review | registry and pinned Debian package | NOT_RUN | pending | pending | owner |
| 611-D | Responsive gallery | every theme/layout rendered at desktop/mobile; responsive bounds; screenshots retained | pending | pinned Chromium | gallery DeckSpec + asset manifest | NOT_RUN | pending | pending | owner |
| 611-E | Reproducibility | Markdown/theme version/manifest preserved; repeated pinned build within documented tolerance | pending | adapter + raster comparator | repeated gallery source and assets | NOT_RUN | pending | pending | owner |
| 611-F | Safe CSS routing | safe theme excludes unsupported CSS; complex editable request blocked without fallback | pending | adapter unit/integration tests | safe/progressive theme fixtures | NOT_RUN | pending | pending | owner |
| 611-G | Editable output | safe-theme PPTX opens in LibreOffice; native object counts and visual comparison recorded | pending | Marp + LibreOffice Impress | safe-theme gallery deck | NOT_RUN | pending | pending | owner |
| 611-H | Receipt/errors | theme/version/layout identities recorded; invalid theme and fallback cases are explicit | pending | adapter tests | positive and invalid synthetic input | NOT_RUN | pending | pending | owner |
| 611-I | PR regression | adapter, canonical model, base integration, theme regression workflow | pending | GitHub Actions | locked regression set | NOT_RUN | pending | pending | owner |
| 611-J | Exact-main regression | final-main Validate, Domain, Site CI and Marp adapter all pass; artifact digest retained | pending | GitHub Actions | exact final source SHA | NOT_RUN | pending | pending | owner |
| runtime-site | Site/package/runtime | not registered or deployed in this scope; no runtime behavior changed | N/A | Site / Cloud Next | N/A | reviewed | N/A | explicit scope boundary | owner |

## Inventory

| Layer | Distinct scenarios | Planned runs | PASS | FAIL | NOT_RUN / BLOCKED | Reviewed N/A |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Registry/layout/contrast | 6 | once per candidate | 0 | 0 | 6 | 0 |
| HTML gallery/responsive/repeat | 4 themes + safe variant, 7 layouts, 2 viewports | twice per candidate | 0 | 0 | 1 | 0 |
| Editable-safe/PPTX reopen | generate, reopen, inspect and compare | once per candidate | 0 | 0 | 1 | 0 |
| Regression/CI | locked sentinels + all required workflows | once per candidate | 0 | 0 | 1 | 0 |
| Site/runtime | 0 | 0 | 0 | 0 | 0 | 1 |

#283 remains open; this matrix cannot be used as evidence for native Figma Slides or client/runtime acceptance.
