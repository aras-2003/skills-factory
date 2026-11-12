# PRES-07 editable-object manual receipt

- **Candidate tree:** Skills Factory main `a271ec42fdb9533e6e9f3cecd4b22982b5902f4d`; identical tree to PR candidate `9e022e29e3a7c5b641c2a16e3dce61e9ba59b1a3` (`58bab57cee49f4e0b9fcc25ff86e97481d792638`).
- **Input:** synthetic 12-slide `deck-editable.pptx`, SHA-256 `e43c551de106b28e7e3db6a00bcde1aea708af24b5a26e7641af095f3edf3d0d`.
- **Application:** desktop LibreOffice Impress on macOS. The installed desktop version was not independently recorded; the pinned CI runtime is LibreOffice 7.4.7.2.
- **Result:** PASS for selecting and saving an actual text-bearing PPTX object and an independent diagram shape, then reopening the edited PPTX and observing its changed geometry.

## Before and after

| Object | Before | Action | After save and reopen |
| --- | --- | --- | --- |
| Slide 1 title text box (`Shape 4`) | x=2.28 cm, y=1.88 cm | Moved right once | x=2.38 cm, y=1.88 cm; size 20.80 × 1.54 cm |
| Slide 5 diagram node rectangle (`Shape 15`, “Canonical DeckSpec”) | x=4.13 cm, y=7.09 cm | Moved right twice | x=4.33 cm, y=7.09 cm; size 6.35 × 2.43 cm |

- **Edited shape-test copy:** `deck-editable-manual-A5.pptx`, SHA-256 `98076a7bf3fd6986a4efefc9dbeb705c9f262f68853c0aa19b6955ee20d3b38d` (retained in the local QA artifact folder).
- **Edited text-test copy:** `deck-editable-manual-test.pptx`, SHA-256 `c75d12fc35094b1f744bda549bc66bef7d6e12017031dc33642ab01886daaf32` (retained in the local QA artifact folder); slide 1 title changed to “Editable title verified”, saved and reopened with the new title visible.
- Both edited copies are disposable QA outputs; the canonical generated PPTX remains unchanged. LibreOffice asked to preserve the PowerPoint 2007–365 format and the files were saved as `.pptx`.
- Before/after UI states and the reopened object geometry were observed in the Codex computer-use session. No screenshot file was exported from that session.
