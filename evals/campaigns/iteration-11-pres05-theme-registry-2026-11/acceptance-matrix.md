# Iteration 11 — PRES-05 acceptance matrix

Baseline: `2ebd353277c5c2551ca345ee89cc9fab711c3d41`. Implementation main SHA (PR #638 merge, exact-code regression target): `48924fe5fc3ccd0e1f56574b08ccfcf08eb6c079`. Scope is #611 only.

| Row | Criterion | Required evidence | Candidate SHA / dependency lock | Runner / tools | Fixture/input hashes | State | Verdict | Output / receipt | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 611-A | Registry | 4+ original styles + editable-safe variant; valid IDs/versions/token metadata | `cd87ceb608f7b7fe599e0cc6757e5aa414f3a1b9`; pinned Marp image `ghcr.io/marp-team/marp-cli:v4.5.1@sha256:3cf660df7b9737f875e57f7169dff0b08d1d3ab604ea2d655ab761102942fa42` | registry validator + PR CI #230 | registry + synthetic gallery | PASS | PASS | PR #638 candidate artifact `13886837971`; `sha256:7339e4fdf1d8162a3004cc608efd248ccb611708db95e9501b009c5be3333169` | owner; self-review |
| 611-B | Layout grammar | 6+ semantic layouts; aliases and invalid layout rejection | `cd87ceb608f7b7fe599e0cc6757e5aa414f3a1b9` | adapter unit tests + PR CI #230 | gallery DeckSpec | PASS | PASS | PR #638 candidate artifact `13886837971` | owner; self-review |
| 611-C | Readability/license | >=4.5:1 text contrast; exact package license/attribution/fallback; no copied templates | `cd87ceb608f7b7fe599e0cc6757e5aa414f3a1b9` | contrast/license tests + source review + PR CI #230 | registry and pinned Debian package | PASS | PASS | PR #638 artifact `13886837971`; registry source review | owner; self-review |
| 611-D | Responsive gallery | every theme/layout rendered at desktop/mobile; responsive bounds; screenshots retained | `cd87ceb608f7b7fe599e0cc6757e5aa414f3a1b9` | pinned Chromium + PR CI #230 | gallery DeckSpec + asset manifest | PASS | PASS | PR artifact `13886837971`; repeated desktop/mobile screenshot checks; user-supplied artifact exposed hidden lazy-loaded slides and the final inspector explicitly reveals the active SVG before capture | owner; self-review |
| 611-E | Reproducibility | Markdown/theme version/manifest preserved; repeated pinned build within documented tolerance | `cd87ceb608f7b7fe599e0cc6757e5aa414f3a1b9` | adapter + raster comparator + PR CI #230 | repeated gallery source and assets | PASS | PASS | PR artifact `13886837971`; repeated screenshot hashes and receipts | owner; self-review |
| 611-F | Safe CSS routing | safe theme excludes unsupported CSS; complex editable request blocked without fallback | `cd87ceb608f7b7fe599e0cc6757e5aa414f3a1b9` | adapter unit/integration tests + PR CI #230 | safe/progressive theme fixtures | PASS | PASS | PR artifact `13886837971`; explicit blocked result verified | owner; self-review |
| 611-G | Editable output | safe-theme PPTX opens in LibreOffice; native object counts and visual comparison recorded | `cd87ceb608f7b7fe599e0cc6757e5aa414f3a1b9` | Marp + LibreOffice Impress + PR CI #230 | seven-slide safe-theme gallery deck | PASS | PASS | PR artifact `13886837971`; variable-size OCR/reopen check validates all seven action titles and image comparison <=0.20 | owner; self-review |
| 611-H | Receipt/errors | theme/version/layout identities recorded; invalid theme and fallback cases are explicit | `cd87ceb608f7b7fe599e0cc6757e5aa414f3a1b9` | adapter tests + PR CI #230 | positive and invalid synthetic input | PASS | PASS | PR artifact `13886837971`; theme regression receipt records resolved font faces | owner; self-review |
| 611-I | PR regression | adapter, canonical model, base integration, theme regression workflow | `cd87ceb608f7b7fe599e0cc6757e5aa414f3a1b9` | GitHub Actions run [#230](https://github.com/aras-2003/skills-factory/actions/runs/43086376364) | locked regression set | PASS | PASS | candidate artifact `13886837971`, `sha256:7339e4fdf1d8162a3004cc608efd248ccb611708db95e9501b009c5be3333169` | owner; self-review |
| 611-J | Exact-main regression | final-main Validate, Domain, Site build/deploy and Marp adapter all pass; artifact digest retained | `48924fe5fc3ccd0e1f56574b08ccfcf08eb6c079`; pinned renderer above | GitHub Actions | exact final main SHA | PASS | PASS | Marp run [#231](https://github.com/aras-2003/skills-factory/actions/runs/43087936141), artifact `13887962875`, `sha256:6961511952bb4c07855ddb58bc9e3b713f613d9bc7b7216a1cbbcb40c2e5a72e`; Validate [#1247](https://github.com/aras-2003/skills-factory/actions/runs/43087936107) PASS; Domain [#1247](https://github.com/aras-2003/skills-factory/actions/runs/43087936169) PASS; Lab/site build [#188](https://github.com/aras-2003/skills-factory/actions/runs/43087936116) PASS; Pages deploy [#314](https://github.com/aras-2003/skills-factory/actions/runs/43087934907) PASS | owner; self-review |
| runtime-site | Site/package/runtime | Cloud Next runtime and production plugin promotion are outside this scope; existing GitHub Pages deploy and source-bound Site build jobs passed after merge | N/A | GitHub Actions | N/A | reviewed | N/A | no Cloud Next runtime acceptance claimed | owner |

## Inventory

| Layer | Distinct scenarios | Planned runs | PASS | FAIL | NOT_RUN / BLOCKED | Reviewed N/A |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Registry/layout/contrast | 4 | once per candidate | 4 | 0 | 0 | 0 |
| HTML gallery/responsive/repeat | 4 themes + safe variant, 7 layouts, 2 viewports | twice per candidate | 2 | 0 | 0 | 0 |
| Editable-safe/PPTX reopen | generate, reopen, inspect and compare | once per candidate | 2 | 0 | 0 | 0 |
| Regression/CI | locked sentinels + all required workflows | PR and exact main | 2 | 0 | 0 | 0 |
| Site/runtime | 0 | 0 | 0 | 0 | 0 | 1 |

#611 is accepted and closed by PR #639. #283 remains open; this matrix cannot be used as evidence for native Figma Slides or Cloud Next runtime acceptance.
