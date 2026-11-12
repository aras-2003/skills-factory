# PRES-08 presentation pilot — preliminary comparison

**State: baseline findings plus candidate changes, not iteration closeout.** This report uses the exact fixture and a reusable CI artifact named by the locked #614 scope. Candidate changes remove the native baseline's visible speaker-note duplication and add repeat-build timing/hash receipts for the five-lane fixture. They have passed scoped local checks but still need final-candidate CI evidence. Manual browser interaction and issue acceptance are incomplete.

## Evidence identity

- Fixture: `pres07-cross-format-v1.json`, SHA-256 `fedb33a0fa2d62c59641d291a7340eb68828a822ca3fa5d71d3275f98954e75e`.
- Rubric: SHA-256 `b3e8f204c9c9e8b277c7576c333bfe5f3f0de96bfb9a9d2634a01e09acf48a22`.
- CI implementation source: `ae8dd753ed8980aa9dd6b188fd4cb1d3feaf27db`; current main `cf6c183bd10e4821224a4a22d405b19c1b5e9d83` differs only in iteration governance documentation. No final #614 candidate artifact has been produced.
- Reusable Actions run: [43266682366](https://github.com/aras-2003/skills-factory/actions/runs/43266682366); artifact [13965669539](https://github.com/aras-2003/skills-factory/actions/runs/43266682366/artifacts/13965669539), archive digest `de00e9de2d1221dcce1363933aeeb306ffe9682bf29dfa0576fff2c316173fd5`.
- Runtime: Marp CLI 4.5.1; Node 26.8.1; Chrome for Testing 153.0.8010.12; LibreOffice 7.4.7.2 in CI. Local Impress 26.8.2.2 was used for manual edit checks.

## Artifact comparison

All four Marp routes use the same 12-slide source and fixture hash. Output hashes below are from the reusable CI artifact. The 12-slide HTML, PDF, flattened PPTX, experimental editable PPTX and native PPTX baseline were reopened in CI; screenshots and machine comparison receipts are included in the linked artifact.

| Route | Output SHA-256 | Observed visual/content facts | Notes and editability |
| --- | --- | --- | --- |
| Marp HTML browser view | `afb52a796c730c543abd7a34e360ed106f04d4d4ec428fdae33000f9bd86af9b` | 12 screenshots at 1280×720. Human review found no clipping or overflow; chart, table, diagram, labels, link and long wrapping remain readable. | HTML is a browser view, not a standalone web-native authoring renderer. CI verifies slide capture and semantics; a manual browser navigation/link interaction is still NOT_RUN. |
| Marp PDF | `34dccae186a8208deaf592d0e12a9ad5c11d4f32e8c563f2f9827c18ea813932` | 12 pages reopened by LibreOffice. All 12 recorded MAE values are below 0.013. Human review found no clipping or overflow. | Stable fixed-layout output; not object-editable. Presenter notes are not supported by experimental Marp editable output; notes remain a separate check. |
| Flattened Marp PPTX | `a9f7815f3c0e269e9e6c666523be3c057562244bc8eed5627b1e8265a81ffe42` | 12 slides reopened. All 12 recorded MAE values are below 0.014. Visual content is close to the HTML/PDF output. | Flattened slide images; do not treat as editable. |
| Experimental editable Marp PPTX | `d44c7077ef8c883c1c0f6cf9f6d854397497612b2b4892ffa9d1d72ae6ec04ec` | 12 slides reopened. All 12 recorded MAE values are below 0.027; largest drift is on slide 4, still well below the 0.20 threshold. Human review found no clipping; diagram text positioning differs slightly. | Bounded title and separate-shape edits persisted after save, close and reopen on a disposable copy. This exporter documents lower fidelity for complex CSS and no presenter notes. |
| Native editable PPTX baseline | `1cac5ae235120d60ba9003499174b92087343cb2c014bc7e4f0138f390c7b49d` | 12 editable slides, native shapes, 12 notes slides and one external hyperlink. Human review found noticeable visual differences: slide 3 chart labels/data are reflowed into bars; slide 4 table becomes pipe-separated text; slide 5 diagram labels/arrows lose their arrangement. In the reusable baseline, notes text appears visibly on the slide render on several slides. | Two bounded text/geometry edits persisted after save, close and reopen on a disposable copy. The candidate generator now keeps note text in speaker notes without putting it on the visible slide. A local ODP smoke check confirmed the visible frame is absent and speaker notes remain; CI must verify the converted/reopened PPTX before treating this fix as accepted. |

The route-specific MAE reports contain 12 `PASS` records each: PDF mean 0.00697 / max 0.01218; flattened PPTX mean 0.00802 / max 0.01306; experimental editable PPTX mean 0.01869 / max 0.02687. These are machine image comparisons, not substitutes for visual review. The native baseline is not included in those three Marp cross-format reports.

## Visual review contact sheets

These contact sheets were built from the CI screenshots named above and cover all 12 slides in each lane. The full-resolution images and per-slide machine reports remain in the Actions artifact.

- [HTML contact sheet](iteration-14-evidence/html-contact-sheet.svg)
- [PDF contact sheet](iteration-14-evidence/pdf-contact-sheet.svg)
- [Flattened PPTX contact sheet](iteration-14-evidence/pptx-flattened-contact-sheet.svg)
- [Experimental editable PPTX contact sheet](iteration-14-evidence/pptx-experimental-contact-sheet.svg)
- [Native PPTX contact sheet](iteration-14-evidence/pptx-native-contact-sheet.svg)

## Decision guidance from current evidence

- Executive and training decks that need interactive browser viewing or reliable fixed-layout review: use the existing Marp HTML/PDF route. Verify the local browser navigation/link behavior before closing the corresponding row.
- Technical decks with editable native objects: use the native PPTX baseline only after addressing its observed layout and note-placement defects; the present baseline fails the visual-usability expectation despite passing basic text/shape editing.
- Experimental editable Marp PPTX: use only when selective text/shape editing has more value than exact diagram/table fidelity. It is not a general replacement for HTML/PDF and must disclose the notes limitation.
- Flattened PPTX: suitable for distribution where appearance is the only requirement; never promise individual object editing.

There is no separate web-native presentation renderer in this repository. Cloud Next is N/A for the export-only scope.

## Remaining acceptance work

- Run the full matrix on the final PR candidate and exact merged `main`; this baseline artifact is not the final-candidate artifact.
- Run the candidate integration workflow, which now records two build durations and output hashes for each of the four Marp routes when the locked PRES-07 fixture is selected, plus first/second HTML screenshot hashes. The candidate receipt has not yet been produced.
- Perform and record a manual HTML browser navigation and source-link interaction. The current browser-control policy refused `file:` URLs, so this remains NOT_RUN; no network-serving workaround was used.
- Recheck the native-baseline note fix in the final converted PPTX. The chart/table/diagram layout differences remain real and must be reflected in content parity, visual review, maintenance and route recommendations.
- Complete failure/security and dependency maintenance inventory with exact candidate receipts; keep any missing/blocked row NOT_RUN or BLOCKED.
- Reconcile the final matrix, PR, Issue #614 and iteration status before any later iteration begins.
