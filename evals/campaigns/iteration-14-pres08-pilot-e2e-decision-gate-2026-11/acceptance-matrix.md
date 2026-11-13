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

## Candidate results — 2026-11-12

The scope-lock statuses above are historical. Results below apply to the merged code tree for PR #658, whose source commit was `bbc775a52fd58f3e7cf34e819f65c5135ec9373e` and exact-main merge was `fd45e13d63dde99108b2129a1a2eacd5cabc7617`. Git tree `68787f0f7b61d870290a8935ba4a5e6ad4fa8ca7` is identical for both SHAs. The submitted PR artifact was SHA-256 `a53f17236a90b0db5e48e8bf8c6b5e704ddf2f4e0035d8bd0c3f613f3aba24b0`; exact-main artifact digest is `sha256:183ca74633b02f8201b4af4a2ab241760ed9a70f6a14cfe13b25ccabd7ef4bb8`.

| Row | Verdict | Evidence / result |
| --- | --- | --- |
| 14-01 | PASS | Fixture SHA `fedb33a0fa2d62c59641d291a7340eb68828a822ca3fa5d71d3275f98954e75e`; rubric SHA `b3e8f204c9c9e8b277c7576c333bfe5f3f0de96bfb9a9d2634a01e09acf48a22`; 12 ordered IDs `qa-01`…`qa-12`. CI validated the canonical fixture and cross-format outputs in [run 43303844082](https://github.com/aras-2003/skills-factory/actions/runs/43303844082). |
| 14-02 | PASS | Headless Chrome reopened 12 HTML slides at 1280×720; HTML SHA `afb52a796c730c543abd7a34e360ed106f04d4d4ec428fdae33000f9bd86af9b`. Interactive navigation/link behavior is separate row 14-11. |
| 14-03 | PASS | PDF reopened: 12 pages, 960×540 pt (16:9), SHA `60fb3a403c72d9fd48ca66dd5f4905ed44ca080036c91e5ef5860d995a9478e0`. |
| 14-04 | PASS | Flattened PPTX reopened: 12 slides, 12192000×6858000 EMU (16:9), 0 native shapes and 12 rasterized slides, 12 notes slides; SHA `04c862eeeb5a5fde28a86536de3a089f7be1c2ce3a78ff699487342e39854168`. |
| 14-05 | PASS | Experimental editable PPTX reopened: 12 slides, 12192000×6858000 EMU (16:9), native shape counts `[8,9,24,49,27,12,9,9,9,11,10,11]`; no notes slides; SHA `0fa741dac3d5c780aa4586bd0152609691aff24923273efd1f6959ad7b6c6238`. |
| 14-06 | PASS | Native PPTX reopened in LibreOffice Impress: 12 slides, 10080625×5670550 EMU (16:9), native shape counts `[3,3,12,3,12,3,3,3,3,4,3,3]`, 12 notes slides, 1 external hyperlink; SHA `86b27df85afd505f7cc4177a0966bfd94fdb2ba0ca12095e31db2025790a7601`. |
| 14-07 | PASS | Same fixture produced all formats. PDF text extraction and route inspections retain source categories and values. Flattened PPTX preserves notes but is raster-only and has no active hyperlink; experimental editable PPTX has no notes or active hyperlink; native PPTX has notes and one hyperlink but represents the diagram as editable boxes plus relationship text rather than the Marp arrows. Losses are explicit, not silently treated as parity. |
| 14-08 | PASS | Human review of contact sheet slides 1–6 across all five lanes found no clipping/overflow or missing glyphs. Native baseline uses a deliberately simpler visual grammar. Contact sheet: `visual-review-slides-01-06.png`. |
| 14-09 | PASS | Human review of contact sheet slides 7–12 across all five lanes found no clipping/overflow or missing glyphs. Contact sheet: `visual-review-slides-07-12.png`. |
| 14-10 | PASS | Disposable Impress copies of both editable PPTX variants were edited, saved, closed and reopened. Title and moved text/shape geometry persisted; native moved object reopened at X 1.20 cm and experimental at X 2.38 cm. Source outputs were not changed. |
| 14-11 | PASS | User confirmed left/right arrow navigation works in Chrome and manually clicked the slide-10 source link. Observed target `https://example.org/pres07/synthetic-reference`; destination displays IANA's notice that `example.org` is reserved for documentation examples and should not be relied on for testing/monitoring. No unexpected failure was reported. Browser product is Chrome; exact version was not provided. |
| 14-12 | PASS | Two identical-input builds: HTML 2170/2165 ms and identical output/screenshot hashes; PDF 3567/3556 ms; flattened PPTX 4699/4644 ms; experimental PPTX 4303/4275 ms. PDF differs only in CreationDate/ModDate; flattened PPTX differs only in `docProps/core.xml`; experimental PPTX ZIP entry payloads are identical. Cross-format MAE (HTML baseline, 12 slides each): PDF max 0.0121758, flat PPTX max 0.0130576, editable PPTX max 0.0268726; every result is below 0.20. |
| 14-13 | PASS | Exact-main Marp run 43303844082 passed adapter unit/security tests, missing-LibreOffice and missing-browser fail-closed checks, output generation/reopen, theme regressions, report-composer and visual-output-design probes, and the mixed diagram/chart/table/SVG checks. Renderer commands use `--network none`. |
| 14-14 | PASS | `decision-report.md` publishes exact source and artifact identities, per-route measurements, screenshots/contact sheets, editability/content losses, limitations and recommendations for executive, technical and training use. It states no standalone web-native renderer exists and Cloud Next is N/A for this export-only scope. |

| Sentinel | Verdict | Evidence |
| --- | --- | --- |
| RS-609 | PASS | Exact-main run 43303844082 passed local-asset/security tests; integration rendering and inspections run with Docker `--network none`. |
| RS-610 | PASS | Exact-main run 43303844082 passed missing-runtime/no-downgrade checks and unsupported editable theme failure. |
| RS-REPORT | PASS | Exact-main run 43303844082 passed report-composer and visual-output-design unchanged-domain probes. |
