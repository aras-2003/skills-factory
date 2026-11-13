# PRES-08 — cross-format pilot decision report

**Status: validated; evidence changes are prepared for review.** This report is bound to the fixture and runtime evidence from PR #658's exact source tree. Implementation source `bbc775a52fd58f3e7cf34e819f65c5135ec9373e` was merged as `fd45e13d63dde99108b2129a1a2eacd5cabc7617`; both have tree `68787f0f7b61d870290a8935ba4a5e6ad4fa8ca7`. The merge result's Presentation Marp workflow [43303844082](https://github.com/aras-2003/skills-factory/actions/runs/43303844082) passed and uploaded exact-main artifact digest `sha256:183ca74633b02f8201b4af4a2ab241760ed9a70f6a14cfe13b25ccabd7ef4bb8`. The visually reviewed PR artifact is SHA-256 `a53f17236a90b0db5e48e8bf8c6b5e704ddf2f4e0035d8bd0c3f613f3aba24b0`.

## Input and runtime

- Fixture: `adapters/presentation-marp/fixtures/pres07-cross-format-v1.json`, SHA-256 `fedb33a0fa2d62c59641d291a7340eb68828a822ca3fa5d71d3275f98954e75e`.
- Rubric: SHA-256 `b3e8f204c9c9e8b277c7576c333bfe5f3f0de96bfb9a9d2634a01e09acf48a22`.
- 12 slides (`qa-01` through `qa-12`); entirely synthetic values and source links.
- Runtime image `ghcr.io/skills-factory/presentation-marp:1.0.0`; Marp 4.5.1, Node 26.8.1, Chrome for Testing 153.0.8010.12, LibreOffice 7.4.7.2. Main adapter artifact digest: `sha256:183ca74633b02f8201b4af4a2ab241760ed9a70f6a14cfe13b25ccabd7ef4bb8`.

## Results by route

| Route | Output and repeat timing | Fidelity / editing / losses |
| --- | --- | --- |
| Marp HTML | `deck.html`, SHA `afb52a796c730c543abd7a34e360ed106f04d4d4ec428fdae33000f9bd86af9b`; 2170/2165 ms; exact output and screenshot hashes repeated. | Existing Marp slide view in Chromium, 12 × 1280×720. Active source-link and keyboard-navigation interaction still needs a manual browser receipt. |
| Marp PDF | `deck.pdf`, SHA `60fb3a403c72d9fd48ca66dd5f4905ed44ca080036c91e5ef5860d995a9478e0`; 3567/3556 ms. | 12 pages at 960×540 pt. Reopened and visually compared. Repeat archive difference is only CreationDate/ModDate metadata. |
| Marp flattened PPTX | `deck.pptx`, SHA `04c862eeeb5a5fde28a86536de3a089f7be1c2ce3a78ff699487342e39854168`; 4699/4644 ms. | Reopened 12-slide 16:9 deck; every slide is a single raster image. Presenter notes remain; there are no active external hyperlinks. Repeat difference is only `docProps/core.xml`. |
| Experimental editable Marp PPTX | `deck-editable.pptx`, SHA `0fa741dac3d5c780aa4586bd0152609691aff24923273efd1f6959ad7b6c6238`; 4303/4275 ms. | Reopened 12-slide 16:9 deck with native shapes. No presenter notes or active external hyperlinks. Repeat ZIP entries have identical payloads despite whole-archive hash difference. Complex CSS is unsupported and fails closed rather than silently flattening. |
| Native editable PPTX baseline | SHA `86b27df85afd505f7cc4177a0966bfd94fdb2ba0ca12095e31db2025790a7601`. | Reopened 12-slide 16:9 deck; native shapes, 12 notes slides and one external hyperlink. It uses simplified chart/table/diagram layout, so editability does not imply visual parity. On slide 5, the native diagram represents relationships as text rather than directional arrows. |

Cross-format image MAE uses the Chromium HTML screenshot as reference: PDF max 0.0121758 (average 0.0069742), flattened PPTX max 0.0130576 (average 0.0080165), experimental editable PPTX max 0.0268726 (average 0.0186907). All 36 measurements pass the 0.20 threshold. Human visual review of both contact sheets found no clipping, overflow or missing glyphs; it also confirmed the native baseline's intentional structural simplifications.

![Slides 1–6 in HTML, PDF, flattened PPTX, experimental editable PPTX and native PPTX order](/Users/arkadiuszkamrowski/.codex/worktrees/pres08-pilot-evidence/skills-factory/evals/campaigns/iteration-14-pres08-pilot-e2e-decision-gate-2026-11/visual-review-slides-01-06.png)

![Slides 7–12 in HTML, PDF, flattened PPTX, experimental editable PPTX and native PPTX order](/Users/arkadiuszkamrowski/.codex/worktrees/pres08-pilot-evidence/skills-factory/evals/campaigns/iteration-14-pres08-pilot-e2e-decision-gate-2026-11/visual-review-slides-07-12.png)

## Object editing and recommendation

On disposable copies in Impress, a title edit and a shape/text-object move survived save, close and reopen for both editable routes. The experimental route's moved object reopened at X 2.38 cm; the native route's at X 1.20 cm. The bounded exercise establishes object-level editing only; it does not prove parity with PowerPoint, visual fidelity, notes support or hyperlink behavior.

- **Executive presentation:** use native PPTX when the deliverable must remain object-editable; use PDF or flattened PPTX when fixed high-fidelity appearance is more important than editing.
- **Technical presentation:** use the Markdown/Marp HTML and PDF/PPTX exports when the reproducible source and strong cross-format fidelity matter. Choose experimental editable PPTX only when editing inside Impress is an explicit requirement and note/link loss is accepted.
- **Training:** use HTML after the manual browser navigation/source-link check passes; otherwise provide PDF or native PPTX with its own editing and link caveats.
- There is no independent web-native slide renderer in the repository. Cloud Next behavior is out of scope and N/A.

The exact-main Marp CI passed unit and input-security tests, missing-browser/LibreOffice fail-closed tests, output generation/reopen, theme regression, report-composer/visual-output-design probes, and mixed exhibit checks. CI runs the renderer with network disabled. The local adapter suite also passed: 21 tests, 0 failures.

## Remaining acceptance gate

The user confirmed that left/right arrow navigation works in Chrome and clicked the slide-10 source link, observing `https://example.org/pres07/synthetic-reference`. The destination displays IANA's reserved-example-domain notice, so it is a placeholder reference rather than a working source service; the URL behavior is expected for the synthetic fixture. Chrome's exact version was not captured. The browser interaction gate is satisfied; all 14 acceptance rows and three sentinels are now PASS, subject to publication of this evidence and issue reconciliation.
