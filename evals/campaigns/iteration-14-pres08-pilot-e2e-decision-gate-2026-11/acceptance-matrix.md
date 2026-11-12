# Iteration 14 / PRES-08 acceptance matrix

Scope-lock ledger for #614. Every row is **NOT_RUN** at scope lock; this file contains planned cases only. Record candidate SHA, exact artifact hashes, runtime identity, evidence links and reviewer with each result. Do not convert an unavailable surface into PASS.

| Row | Criterion | Surface / case | Planned evidence and pass condition | Status |
| --- | --- | --- | --- | --- |
| 14-01 | 614-A1 | Shared input identity | Fixture and rubric hashes match the scope record; 12 slide IDs/order, claims, values, links and notes are inventoried. | NOT_RUN |
| 14-02 | 614-A2 | Marp HTML | Exact-candidate HTML opens in browser; 12 slides, dimensions, navigation and payload hash recorded. | NOT_RUN |
| 14-03 | 614-A2 | Marp PDF | Exact-candidate PDF reopens; 12 pages, dimensions, runtime/version and hash recorded. | NOT_RUN |
| 14-04 | 614-A2 | Marp flattened PPTX | Exact-candidate PPTX reopens; 12 slides, dimensions, runtime/version and hash recorded. | NOT_RUN |
| 14-05 | 614-A2 | Experimental editable PPTX | Exact-candidate output reopens; slide count, dimensions, conversion versions and hash recorded. | NOT_RUN |
| 14-06 | 614-A2 | Native editable PPTX baseline | Native baseline reopens; slide count, dimensions, authoring/runtime identity and hash recorded. | NOT_RUN |
| 14-07 | 614-A3 | Content parity across five lanes | Compare title, claim, category, value/unit, chart labels, sources and notes per slide; all losses are explicit and no silent value/category loss occurs. | NOT_RUN |
| 14-08 | 614-A4 | Visual review, slides 1–6 | Comparable screenshots/contact sheet for each applicable lane; log clipping, overflow, wrapping, glyph and contrast/link issues; compute image MAE (≤0.20) and complete human review. | NOT_RUN |
| 14-09 | 614-A4 | Visual review, slides 7–12 | Same evidence and gate as 14-08 for the remaining slides. | NOT_RUN |
| 14-10 | 614-A5 | Desktop object edit | In Impress, change title text and move a shape on disposable copies of experimental and native PPTX; save, close, reopen, verify persisted edits; record notes/links separately. | NOT_RUN |
| 14-11 | 614-A5 | Browser interaction | Verify HTML navigation and source-link behavior in a browser; capture browser/runtime identity and any failures. | NOT_RUN |
| 14-12 | 614-A6 | Repeatability and timing | Two builds per applicable output lane from identical pinned inputs/dependencies; record elapsed time, output/screenshot hashes and distinguish deterministic generation from conversion drift. | NOT_RUN |
| 14-13 | 614-A7 / 614-A8 | Failure, security, maintenance | Confirm missing browser/LibreOffice and unsupported theme fail closed; no silent downgrade; network disabled. Inventory dependencies, conversion steps, operator actions and evidence-backed limitations. | NOT_RUN |
| 14-14 | 614-A9 | Decision report and routing | Publish source/artifact identities, comparison, screenshots/contact sheets, measurements, limitations and evidence-backed executive/technical/training route recommendations. State no standalone web-native renderer; Cloud Next is N/A. | NOT_RUN |

## Shared regression sentinels

| Sentinel | Contract | Planned evidence | Status |
| --- | --- | --- | --- |
| RS-609 | Local-asset/network/security contract | Run the existing relevant checks against the locked candidate; show the renderer makes no network requests. | NOT_RUN |
| RS-610 | No-silent-downgrade routing contract | Exercise unsupported format/theme and missing tool paths; each must fail closed with a bounded actionable diagnostic. | NOT_RUN |
| RS-REPORT | Report composer and visual-output-design unchanged-domain probes | Run existing regression probes and attach run links/results to the final candidate record. | NOT_RUN |

## Result record template

For every completed row, add: verdict and timestamp (UTC); candidate main SHA; input, output and screenshot hashes as applicable; command/tool and version; artifact or run URL; observed facts; deviations; reviewer. A row passes only when all listed evidence is present and the stated condition is met. Preserve superseded results and mark invalidated rows with the replacement candidate.