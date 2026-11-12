# PRES-08 editable-object manual receipt

**State: baseline evidence recorded; final candidate CI and closeout remain pending.**

- **Locked fixture:** `adapters/presentation-marp/fixtures/pres07-cross-format-v1.json`, SHA-256 `fedb33a0fa2d62c59641d291a7340eb68828a822ca3fa5d71d3275f98954e75e`.
- **Locked rubric:** SHA-256 `b3e8f204c9c9e8b277c7576c333bfe5f3f0de96bfb9a9d2634a01e09acf48a22`.
- **Baseline CI source:** `ae8dd753ed8980aa9dd6b188fd4cb1d3feaf27db`; the current main descendant `cf6c183bd10e4821224a4a22d405b19c1b5e9d83` differs only in the two iteration governance documents. The final #614 evidence candidate has not yet been built.
- **CI artifact:** run [43266682366](https://github.com/aras-2003/skills-factory/actions/runs/43266682366), artifact [13965669539](https://github.com/aras-2003/skills-factory/actions/runs/43266682366/artifacts/13965669539), archive SHA-256 `de00e9de2d1221dcce1363933aeeb306ffe9682bf29dfa0576fff2c316173fd5`.
- **Generated outputs:** native PPTX `1cac5ae235120d60ba9003499174b92087343cb2c014bc7e4f0138f390c7b49d`; experimental editable PPTX `d44c7077ef8c883c1c0f6cf9f6d854397497612b2b4892ffa9d1d72ae6ec04ec`.
- **Application:** LibreOffice Impress 26.8.2.2. The pinned CI conversion runtime is LibreOffice 7.4.7.2.
- **Result:** PASS for the bounded manual editing exercise on disposable local copies of both baseline outputs. The actual saved copies were closed and reopened before checking the text and geometry in Impress.

| Output | Object before | Action | Value after reopening |
| --- | --- | --- | --- |
| Native editable PPTX | Slide 1 title `One source, five output formats`; separate Body shape at X 1.00 cm | Replaced title text and pressed Right once on the Body shape | Title `Native edit verified`; Body X 1.10 cm |
| Experimental editable PPTX | Slide 1 title `One source, five output formats`; separate subtitle text shape at X 2.28 cm | Replaced title text and pressed Right once on the subtitle shape | Title `Experimental edit verified`; subtitle shape X 2.38 cm |

| Disposable copy | SHA-256 after save and reopen |
| --- | --- |
| Native baseline copy `native-baseline-manual-copy.pptx` | `f55178003f0098a5007b8eae058bf86cfa45c8a4c8bc00adf85316d9b6395f47` |
| Experimental editable copy `experimental-editable-manual-copy.pptx` | `d192c27b65e15fede3252f3a65871688b9af3a7a6f194e7979eeaa4306314d8c` |

The generated source PPTX files were not changed. The manual copies are temporary local test data and are not included in the repository. The assessment covers object text and geometry persistence only; it does not imply visual fidelity or notes support.
