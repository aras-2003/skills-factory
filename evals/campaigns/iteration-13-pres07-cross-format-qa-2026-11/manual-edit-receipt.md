# PRES-07 editable-object manual receipt

- **Code candidate:** PR #651 source `c0cf0d45c7b290a0297380a0f8ab327b58c3d162`.
- **Generated artifact:** `sf-presentation-marp-c0cf0d45c7b290a0297380a0f8ab327b58c3d162`, 12 slides; editable PPTX SHA-256 `c087a16784ad16c4999c45b928e733b103168e04fa95e6aaa4a57df58b5201fc`.
- **Application:** LibreOffice Impress 26.8.2.2 (`9dea406ab7695df6325b11b0e19fdca8db4b7276`). The CI renderer uses LibreOffice 7.4.7.2.
- **Result:** PASS. In a disposable copy of the exact generated PPTX, changed a title and moved a separate shape. Both changes remained after save, close and reopen.

| Object | Before | Action | After reopening |
| --- | --- | --- | --- |
| Slide 1 title text box | Original fixture title | Replaced with `Editable title verified` | Updated title visible in slide and Impress accessibility tree |
| Slide 5 shape, “Receipts and verdicts” | X 5.04 cm, Y 9.53 cm; 4.53 × 0.58 cm | Pressed Right once while the shape was selected | X 5.24 cm, Y 9.53 cm; 4.53 × 0.58 cm; label text unchanged |

- **Edited disposable copy:** `deck-editable-manual-c0cf0d45.pptx`, SHA-256 `b5ebd802833ba42b1d4a51c41abc5a07bb2b1b08f885baf8c9efb297b3bfed5b`.
- The generated artifact remains unchanged. After reopening, the title text and selected shape position were read from Impress; no UI screenshot was saved.
- The user-supplied ZIP has SHA-256 `da95e338e5dac1332ad5a848e03c6bc9fe9d0b4d4c8c80d50f4818c296b4cb65` and contains a 12-slide artifact for earlier source `28c7cbad71aaa629e400c1fc5ab48bf358083b59`. It is not the c0 artifact and is not used for this manual receipt.
