# PRES-07 editable-object manual receipt

- **Candidate:** PR #651 head `c0cf0d45c7b290a0297380a0f8ab327b58c3d162`.
- **Artifact:** `sf-presentation-marp-c0cf0d45c7b290a0297380a0f8ab327b58c3d162`, SHA-256 `03c1453f71b3966c71e069923d97e169e2518355f4b611e16f494a8ff8af732f`.
- **Input:** generated experimental editable deck, SHA-256 `c087a16784ad16c4999c45b928e733b103168e04fa95e6aaa4a57df58b5201fc`.
- **Application:** LibreOffice Impress 26.8.2.2 (`9dea406ab7695df6325b11b0e19fdca8db4b7276)); CI runtime is LibreOffice 7.4.7.2.
- **Result:** Partial. A real title text edit was saved and persisted after reopening. A shape move has **not** been verified on this exact candidate; the older b584 receipt is not transferable to c0.

| Object | Before | Action | After reopening |
| --- | --- | --- | --- |
| Slide 1 title text box | Original fixture title | Replaced with `Editable title verified` in a disposable copy | New title visible on slide 1 and in the accessibility tree |
| Slide 5 diagram object | Original position | Not completed on c0 | No geometry-change claim |

- **Edited disposable copy:** `deck-editable-manual-c0cf0d45.pptx`, SHA-256 `82cc5ba15dc384b79b67766a6b51ce10e717d70db41898f3d4a4440e5dbce488`.
- The canonical generated PPTX was left unchanged. The text edit was observed after saving and reopening the copy in Impress. No screenshot was exported from the UI session.
- **Acceptance:** exact-candidate shape-move gate remains NOT_RUN; this receipt does not close issue #613.
