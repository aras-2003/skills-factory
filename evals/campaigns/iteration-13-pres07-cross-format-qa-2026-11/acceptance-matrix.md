# Iteration 13 acceptance matrix

Candidate source starts at main `56a28aff02897de103f2e7b6b9825caa6222a19a`. This is a scope-locked plan; a green CI run does not satisfy manual PowerPoint edit or runtime inspection. The attached 3-slide artifact is pre-lock historical evidence and is not counted.

| Row ID | Issue / criterion | Layer + case ID / definition | Required / N/A rationale | Candidate SHA + artifact digest | Surface/model/tools | Input/rubric hashes | Execution state | Verdict | Receipt/output/trace + run time | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 613-A1-fixture | #613 / A1 | Generate 12-slide synthetic reference deck; assert exact slide IDs, expected text/data/provenance and required semantic features | Required | pending | Canonical DeckSpec validator | pending | NOT_RUN | none | pending | owner |
| 613-A2-html | #613 / A2 | Render, reopen HTML; assert slide count, 16:9 dimensions, semantic text, links and screenshot capture | Required | pending | pinned Marp + Chromium | pending | NOT_RUN | none | pending | owner |
| 613-A2-pdf | #613 / A2 | Render and reopen PDF; assert page count/dimensions/text/links and images | Required | pending | pinned Marp/Chromium + Poppler | pending | NOT_RUN | none | pending | owner |
| 613-A2-flat-pptx | #613 / A2,A5 | Render/reopen flattened PPTX; assert page geometry, notes and image-only slide elements; classify as non-editable | Required | pending | Marp + LibreOffice | pending | NOT_RUN | none | pending | owner |
| 613-A2-editable-pptx | #613 / A2,A5 | Render/reopen experimental editable PPTX; inspect shapes, text and notes limitation | Required | pending | Marp + LibreOffice | pending | NOT_RUN | none | pending | owner |
| 613-A2-native-pptx | #613 / A2,A5 | Open generated native PPTX baseline and compare semantic content, geometry and objects | Required | pending | Microsoft PowerPoint | pending | NOT_RUN | none | pending | owner |
| 613-A3-content-html | #613 / A3 | Compare titles, claims, categories, data, units, source links and labels against fixture | Required | pending | HTML parser + assertions | pending | NOT_RUN | none | pending | owner |
| 613-A3-content-pdf | #613 / A3 | Extract PDF content and compare values/categories/units/links/notes where supported | Required | pending | Poppler + assertions | pending | NOT_RUN | none | pending | owner |
| 613-A3-content-pptx | #613 / A3 | Extract flattened/editable/native PPTX text/data/notes; detect mutation or omissions | Required | pending | OOXML inspector + PowerPoint | pending | NOT_RUN | none | pending | owner |
| 613-A4-html-visual | #613 / A4 | Compare all slide images; check overflow, clipping, contrast, missing glyphs and link affordances | Required | pending | Chromium screenshots + image diff + review | pending | NOT_RUN | none | pending | owner |
| 613-A4-pdf-visual | #613 / A4 | Reopened PDF page screenshot comparison and per-slide defect review | Required | pending | Poppler screenshots + review | pending | NOT_RUN | none | pending | owner |
| 613-A4-flat-pptx-visual | #613 / A4 | Reopened flattened PPTX visual comparison vs source and PDF; note fidelity/notes behavior | Required | pending | LibreOffice + screenshots | pending | NOT_RUN | none | pending | owner |
| 613-A4-editable-pptx-visual | #613 / A4 | Reopened experimental editable PPTX comparison; record line-wrap, fonts and geometry drift | Required | pending | LibreOffice + screenshots | pending | NOT_RUN | none | pending | owner |
| 613-A5-flat-not-editable | #613 / A5 | Assert flattened Marp output has no native slide text/shape objects and never emits editable PASS | Required | pending | OOXML inspection | pending | NOT_RUN | none | pending | owner |
| 613-A5-editable-manual | #613 / A5 | Select, move/edit/reformat actual PPTX text and shape/chart objects in PowerPoint; save and reopen; retain before/after evidence | Required | pending | Microsoft PowerPoint desktop | pending | NOT_RUN | none | pending | owner |
| 613-A6-repeat-build | #613 / A6 | Two builds from identical source/dependencies; compare content, deterministic outputs and conversion drift separately | Required | pending | pinned CI renderer | pending | NOT_RUN | none | pending | owner |
| 613-A7-missing-lo | #613 / A7 | Request editable PPTX with LibreOffice absent; assert bounded BLOCKED/FAIL and no format downgrade | Required | pending | no-LibreOffice image | pending | NOT_RUN | none | pending | owner |
| 613-A7-missing-browser | #613 / A7 | Request browser-backed output without browser; assert explicit BLOCKED/FAIL and no false receipt | Required | pending | no-browser image | pending | NOT_RUN | none | pending | owner |
| 613-A7-complex-css | #613 / A7 | Exercise complex-theme editable conversion; report unsupported behavior explicitly | Required | pending | Marp + LibreOffice | pending | NOT_RUN | none | pending | owner |
| 613-A8-routing-sentinel | #613 / A8 | Existing #610 routing/editability contract; requested editable mode cannot silently flatten | Required | pending | unit + integration CI | pending | NOT_RUN | none | pending | owner |
| 613-A8-security-sentinel | #613 / A8 | Existing #609 local asset/network/security contract | Required | pending | unit + integration CI | pending | NOT_RUN | none | pending | owner |
| 613-A8-report-probe | #613 / A8 | report-composer artifact opt-in/evidence preservation unchanged-domain probe | Required | pending | Python regression CI | pending | NOT_RUN | none | pending | owner |
| 613-A8-visual-probe | #613 / A8 | visual-output-design factual-chart provenance/capability boundary unchanged-domain probe | Required | pending | Python regression CI | pending | NOT_RUN | none | pending | owner |

## Inventory and execution totals

| Layer / surface | Required distinct scenarios | Planned executions / repetitions | Executed PASS | Executed FAIL | NOT_RUN / BLOCKED / REVIEW_REQUIRED | Reviewed N/A | Evidence compatibility |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fixture/model and semantics | 1 | PR + exact main (2) | 0 | 0 | 1 | 0 | pending |
| HTML/PDF content and visual | 6 | PR + exact main (12) | 0 | 0 | 6 | 0 | pending |
| Flattened/editable/native PPTX inspection | 8 | 7 automated cases on PR + exact main, manual edit once on final candidate (15) | 0 | 0 | 8 | 0 | pending |
| Determinism and failure handling | 4 | PR + exact main (8) | 0 | 0 | 4 | 0 | pending |
| Shared regression probes | 4 | PR + exact main (8) | 0 | 0 | 4 | 0 | pending |
| **Total** | **23** | **45** | **0** | **0** | **23** | **0** | pending |

Completeness review: every frozen criterion has a row; all required rows are NOT_RUN at scope lock. CI rows cannot substitute for the required manual editable-object evidence. No required surface is N/A.
