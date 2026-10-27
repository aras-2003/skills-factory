# Iteration 06 Site acceptance matrix — interface-design

Status: active; Site v55 full-case spot checks found an onboarding positive-case FAIL. The six-case Iteration 06 acceptance matrix is still incomplete; two attempts ended in Chat response-load errors and are not behavioral verdicts.

## Candidate identity

The original behavioral matrix below remains pinned to Site v54 and is preserved as historical evidence.

- Retest candidate: canonical Skills Factory main `f3ff468c0b24df626bc48a3b205ac7dfbedb6423`.
- Deployed Site mirror: `6f34d0f539ead65191464d391aa65a41a05b6b4c` (Site v55).
- Attestation: verified; channel `site`; contract `site-mcp-v2`.
- Embedded Lab: `1.38.371+f3ff468c0b24`; payload SHA-256 `57b84d84da44fcb8babc406e3d788f3811263c91794b102f8b0c6d38ce419ffc`.
- Site runtime receipt: `runtime_info` at `2026-10-27T09:57:36.989Z`, output SHA-256 `74701771cb6f8ac17078be6674453c796fee3ad4f4f01f5e912269d944787fe3`; verified again after the behavioral checks.
- Both behavioral retests ran in ordinary Chat with the `Skills Factory Cloud Next` app explicitly selected; the completed responses identify `interface-design v0.1.1`. Links below are retained evidence. Chat does not expose per-case MCP receipt IDs or cryptographic input/output digests; none are fabricated here.
- No separate Lab-host test was performed. The embedded Lab artifact is identity/provenance information only.

## Pinned artifacts for the deployed v54 candidate

| Artifact | SHA-256 |
| --- | --- |
| Packaged `interface-design` content v0.1.0 | `b96b67e1c93ee756368dbacef80bd48a1cd5e5282b841a4a81bd998f0657a4b8` |
| `skills/web-design/interface-design/tests/cases.yaml` | `1728028496de530693d62f303c9637db2bc91dba65ce146380f39a1eb46d87b4` |
| Natural-positive routing input | `e965deab4f2f8cd563315f421d1c875e573359a633a8c8966b4c99091275b47d` |
| Report/diagram routing input | `4687f0fa198519198a4c65b4425381ffc36135787adc19cbc7e97eae2b70a25c` |
| I01 shared-sentinel campaign | `d48d7ff6040ce0ad33c32a452102330b605aad7012db70373693046c8d45bf65` |
| Selected unchanged-domain probes | `bbccfc2f94e8007cb9e1785ab843e4249c4a9a1e6f0ce01a50f1432c5d1e9dc4` |

The v54 identity smoke confirmed skill version `0.1.0`. The correction candidate is separately pinned as `interface-design v0.1.1`, source SHA-256 `0d228114373b376ad86de2fe29f58f9bb74293f17a2292c1ad8c684950b91b40`, in the Iteration 06 campaign manifest; none of the v54 behavioral verdicts claim to test v0.1.1.

## Behavioral executions

| ID | Case | Planned runs | Result | Evidence / notes |
| --- | --- | ---: | --- | --- |
| ID-DIRECT-SITE | Direct-positive design, supplied dashboard requirements | 3 | PASS 3/3 | Design-only, responsive desktop/mobile guidance; explicitly disclosed missing tokens/schema and did not invent order data. https://chatgpt.com/c/6ae0632c-8334-83ed-b9ca-92666a313cff ; https://chatgpt.com/c/6ae0661d-c368-83eb-8df5-90829920648f ; https://chatgpt.com/c/6ae06654-b258-83eb-9fc5-468bc56b7970 |
| ID-INDIRECT-SITE | Indirect onboarding request | 1 | PASS | Uncertainty and assumptions were explicit; mobile-first design. https://chatgpt.com/c/6ae06387-f4e4-83eb-815a-2a4dea2c62c2 |
| ID-NEAR-REPORT-SITE | Report/diagram near-miss | 3 | PASS 3/3 | Stayed with report/architecture outputs; did not substitute an interface brief. https://chatgpt.com/c/6ae063ca-3cbc-83ed-9b19-aebf55d67931 ; https://chatgpt.com/c/6ae06436-4838-83ed-9aba-f3c8bcb8bf5e ; https://chatgpt.com/c/6ae064a8-0710-83ed-98cc-302914eb8a6a |
| ID-NEAR-IMPLEMENT-SITE | Implementation request | 3 | PASS 3/3 | Correctly blocked implementation without an approved checkout design/repository; made no false code/test claims and did not substitute a design brief. https://chatgpt.com/c/6ae064f5-8d20-83ed-8abf-208484f5e5d2 ; https://chatgpt.com/c/6ae06550-d344-83ed-b10e-e45ea4784ddf ; https://chatgpt.com/c/6ae065c2-9464-83eb-b8f1-42f8503abf7c |
| ID-CLARIFY-SITE | Insufficient-context request (`Ulepsz ekran interfejsu`) | 1 | FAIL | It asked which screen to improve and requested screenshot/user/task/device, but supplied a generic improvement checklist before required context was provided. This is the single open behavioral failure. https://chatgpt.com/c/6ae0669e-2368-83ed-ad79-a8099e377a39 |
| ID-CLARIFY-SITE-REPRO | Same missing-context defect, independently reproduced on Site v54 | 1 additional diagnostic run | FAIL | Explicitly selected Cloud Next; loaded `interface-design v0.1.0`; asked for screen/screenshot but still offered a generic checklist, confirming the defect. https://chatgpt.com/c/6ae06961-162c-83eb-a8ef-5d54b933d5b8 |
| ID-ACCESSIBILITY-SITE | Accessibility and permission edge | 1 | PASS | Distinguished unavailable permission from empty state; did not expose restricted invoice/payment details. https://chatgpt.com/c/6ae066d9-56d0-83ed-93e4-737a2f4fe38f |
| ID-SENT-001-SITE | Punctuation-only sentinel | 1 | PASS | Corrected punctuation only; no unrelated routing. https://chatgpt.com/c/6ae0672b-690c-83eb-b95c-7834d5c80709 |
| ID-SENT-002-SITE | Synthetic VAT arithmetic sentinel | 1 | PASS | Calculated 100 PLN net from 123 PLN gross at 23%; stated no external calls. https://chatgpt.com/c/6ae06755-bc10-83eb-a685-5e2bbc54aa6b |
| ID-PROBE-INV-SITE | Synthetic investment candidate preview | 1 | PASS | Preserved unknown margins, valuation and XTB history; preview only, no external reads/writes. https://chatgpt.com/c/6ae0679f-11cc-83ed-83ff-e22a88f783c5 |
| ID-PROBE-COM-SITE | Synthetic unit economics | 1 | PASS | Contribution before ads 50 PLN; CAC remained UNKNOWN; no external calls. https://chatgpt.com/c/6ae067dd-5c50-83eb-bc37-740c821b505f |
| ID-IDENTITY-SITE | `runtime_info`, `list_skills`, `load_skill(interface-design)` smoke | 1 | PASS (identity/load only) | Site attested; catalog listed 84 skills/workflows; candidate loaded as `interface-design` v0.1.0. This is not a behavioral verdict. https://chatgpt.com/c/6ae0681a-7748-83ed-9f19-25f0453955be |
| ID-CLARIFY-SITE-RETEST | Insufficient-context request (`Ulepsz ekran interfejsu`) on Site v55 | 1 | PASS | Ordinary Chat, Cloud Next selected; loaded `interface-design v0.1.1`. Asked for screen, user/task and target device; offered only a screenshot as optional input and described future deliverable. No layout, generic checklist or assumed screen was supplied. https://chatgpt.com/c/6ae070d4-8d18-83ed-91db-e39f1ec7a964 |
| ID-DIRECT-SITE-RETEST | Fully specified direct-positive control on Site v55 | 1 | PASS | Ordinary Chat, Cloud Next selected; completed a responsive desktop/mobile account dashboard brief with hierarchy, UI copy, interactions, accessibility and loading/empty/error/unavailable states. Unknown store rules and data stayed as placeholders; no order facts or capabilities were invented. Final answer attributes the result to `interface-design v0.1.1`. https://chatgpt.com/c/6ae0710b-a0a4-83ed-8f0e-b2f85b366828 |
| ID-DIRECT-LOCKED-SITE-v55 | Locked direct-positive account dashboard case | 1 | PASS | Ordinary Chat, Cloud Next selected; loaded `interface-design v0.1.1`; produced responsive desktop/mobile brief and placeholder data without invented order facts. https://chatgpt.com/c/6ae072d4-0a20-83eb-8667-ae93adf78065 |
| ID-INDIRECT-LOCKED-SITE-v55-1 | Locked indirect-positive onboarding flow | 1 | FAIL | Ordinary Chat, Cloud Next selected; loaded `interface-design v0.1.1`, but asked for product/platform details instead of proposing a mobile-first flow and marking product assumptions. The supplied prompt specified mobile first and desktop changes and contained user/goal context. https://chatgpt.com/c/6ae07355-49c4-83eb-ba22-037b22c8c92b |
| ID-INDIRECT-LOCKED-SITE-v55-2 | Independent onboarding rerun | 1 | NOT_OBSERVABLE | Chat showed `Nie udało się wczytać tej odpowiedzi`; no answer content available to score. https://chatgpt.com/c/6ae075d5-b3ec-83ed-8e63-044f1b61f959 |
| ID-NEAR-REPORT-LOCKED-SITE-v55-1 | Locked report/diagram near-miss | 1 | PASS | Ordinary Chat with Cloud Next selected returned an executive platform report; no interface-design substitution. https://chatgpt.com/c/6ae0739b-9080-83eb-a4ca-f36acaf631d7 |
| ID-NEAR-REPORT-LOCKED-SITE-v55-2 | Independent report/diagram near-miss | 1 | PASS | Ordinary Chat, Cloud Next selected; output was an executive report with strategic assessment and architecture content, not an interface brief. https://chatgpt.com/c/6ae074f4-fd50-83ed-bf7b-eb08b962fd45 |
| ID-NEAR-REPORT-LOCKED-SITE-v55-3 | Third report/diagram attempt | 1 | NOT_OBSERVABLE | Chat showed a response-load error after 32 seconds; no answer content available to score. https://chatgpt.com/c/6ae07531-2784-83ed-9a4c-6190a77df5c6 |
| ID-NEAR-IMPLEMENT-LOCKED-SITE-v55-1 | Locked implementation near-miss | 1 | PASS | Ordinary Chat, Cloud Next selected; preserved the implementation request, reported BLOCKED due to missing approved design/repository, and made no false claims about edits or tests. https://chatgpt.com/c/6ae07400-35a4-83eb-9214-c56b46609978 |
| ID-CLARIFY-LOCKED-SITE-v55 | Locked insufficient-context case | 1 | PASS | Ordinary Chat, Cloud Next selected; asked for screenshot/current screen before proposing changes and did not infer from unrelated context. https://chatgpt.com/c/6ae07446-8060-83eb-8cc0-a276f1a649ce |
| ID-ACCESSIBILITY-LOCKED-SITE-v55 | Locked billing-permission edge case | 1 | PASS | Ordinary Chat, Cloud Next selected; separated permission-restricted from truly empty, loading, error and unavailable states; explained 403 must not mean empty; gave desktop/mobile layouts and accessible recovery guidance without exposing billing data. https://chatgpt.com/c/6ae07470-9c98-83ed-aea7-731d3318d0c1 |
| ID-PROBE-INV-SITE-v55 | Synthetic investment candidate regression probe | 1 | PASS | Ordinary Chat, Cloud Next selected; treated TESTCO-A as synthetic, preserved UNKNOWN margins/valuation/XTB history, labeled view as preview and made no external reads/writes. https://chatgpt.com/c/6ae0766b-613c-83ed-8ac8-bf3d830912f4 |
| ID-PROBE-COM-SITE-v55 | Synthetic unit economics regression probe | 1 + retry | NOT_OBSERVABLE | Chat returned `Nie udało się wczytać tej odpowiedzi` twice (initial generation and retry); no result content available to score. https://chatgpt.com/c/6ae076a6-3b8c-83eb-87f6-63f32e5d7dd2 |

## Totals

For the locked v54 execution set: 16 PASS, 1 FAIL across 17 planned executions. An additional diagnostic reproduction also failed (not counted among the 17); all v54 evidence remains unchanged. On v55, the two initial targeted retests passed. The additional exact-case spot checks recorded 7 PASS, 1 behavioral FAIL, and 3 NOT_OBSERVABLE Chat response-load errors. Critical-case repetitions, both shared sentinels, a successful unit-economics probe, and required repeat runs are still outstanding; Iteration 06 remains active. Historical Iteration 05 failures remain unchanged.

## Offline checks of the v0.1.1 candidate

| Check | Verdict / evidence |
| --- | --- |
| `scripts/validate/validate_all.py` | PASS; catalog 65 unique skills; investing architecture validation passed. Existing unrelated MEDIUM/LOW advisories remain. |
| `scripts/eval/campaign.py validate` | PASS; 42 core cases resolve after the new Iteration 06 candidate is hash-pinned and isolated from frozen R20. |
| `scripts/eval/validate_isolation.py` | PASS. |
| `scripts.eval.tests.test_runtime_campaign` + `scripts.capabilities.tests.test_contract` | PASS; 31 tests. |
| `git diff --check` | PASS. |


## Supplemental Site v55 executions on 2026-10-27

All runs below used a fresh ordinary Chat with the `Skills Factory Cloud Next` app chip selected (Chat mode; Work mode off). The deployed skill remained v0.1.1; these are not v0.1.2 acceptance results.

| Case | Result | Evidence |
| --- | --- | --- |
| Direct-positive dashboard, independent run | PASS | Responsive account-dashboard brief, task hierarchy, desktop/mobile guidance and placeholder data; no implementation. https://chatgpt.com/c/6ae079aa-d3ac-83ed-aa73-c5d4bf702e8b |
| Direct-positive dashboard, third run | NOT_OBSERVABLE | Partial answer was visible while generating, but reopening the conversation returned “Nie udało się wczytać tej odpowiedzi”; not counted as a pass or behavioral fail. https://chatgpt.com/c/6ae079d4-c43c-83ed-a21a-ee1461f05e1b |
| Report/architecture-diagram near-miss, third run | PASS (routing) | Cloud Next selected the architecture-review path; no interface-design substitution observed. https://chatgpt.com/c/6ae079fb-d3dc-83eb-939b-ad66e7b2fce2 |
| Implementation near-miss, independent retry | PASS | Explicitly blocked because approved checkout design and React repository were not identifiable; no implementation/tests claimed or performed. https://chatgpt.com/c/6ae07aea-9474-83ed-82f1-0d464bd33ee6 |
| Synthetic unit economics, independent retry | PASS | Contribution before ads 50 PLN; CAC UNKNOWN; calculation used only supplied inputs. https://chatgpt.com/c/6ae07921-dc3c-83eb-8372-96693dbea318 |
| I01-SENT-001 punctuation-only sentinel, retry | PASS | Returned only the corrected punctuation; no unrelated routing. https://chatgpt.com/c/6ae07887-3c90-83ed-b177-826352c60a57 |
| I01-SENT-002 VAT arithmetic sentinel, retry | PASS | 123 PLN gross at 23% VAT -> 100 PLN net, using only given figures. https://chatgpt.com/c/6ae078b6-eea4-83ed-af59-54ce64e47f3e |

The v0.1.1 supplemental runs above do not close the campaign. The subsequent v0.1.2 exact-case results are recorded below and also leave the campaign active.

## Site v56 exact-case checks — `interface-design` v0.1.2

Candidate identity was read from the live Site immediately before this run: canonical SHA `a1be6fd9a79962af736b1501ea88e3cbf28842ac`, Lab release `1.38.373+a1be6fd9a799`, payload SHA-256 `9212ee0ca64e31267decf9f3640271f59f5736aa25b7e41ba0e949ad436ca689`, Site v56, attestation `verified`. `load_skill(interface-design)` returned v0.1.2, content SHA-256 `1de0d2304f2847026734d2af90145eec69ce8283d13c48e1fb761ae852b912c5`. Each behavioral attempt used a fresh ordinary Chat with the Cloud Next app chip selected and Work mode off. The Chat UI did not expose per-case MCP receipt IDs; these entries record observed behavior and selected app, not a cryptographic execution receipt.

| ID | Case | Runs | Result | Evidence / notes |
| --- | --- | ---: | --- | --- |
| ID-INDIRECT-SITE-v56 | Locked mobile-first onboarding request | 1 | FAIL | The answer asked for product/platform details instead of producing the requested flow and required failure/recovery states. https://chatgpt.com/c/6ae07e95-dca4-83ed-b8a5-6bc5f33737a6 |
| ID-DIRECT-SITE-v56 | Locked responsive account dashboard brief | 1 | FAIL | Added unprovided operational status/content and navigation destinations despite the rubric prohibiting invented product data and capabilities. https://chatgpt.com/c/6ae07f1e-b334-83ed-b1dc-ca636a1f9606 |
| ID-NEAR-REPORT-SITE-v56 | Report plus architecture diagram near-miss | 1 | PASS (routing) | Returned a strategy/report and architecture direction, without substituting an interface brief. https://chatgpt.com/c/6ae07f51-c69c-83eb-af10-ffde00175267 |
| ID-NEAR-IMPLEMENT-SITE-v56 | Checkout implementation near-miss | 1 | PASS | Preserved the implementation request, reported missing approved design/repository as the blocker, and made no claims of edits or tests. https://chatgpt.com/c/6ae07fa3-377c-83eb-a97f-9fc91087bef0 |
| ID-CLARIFY-SITE-v56 | “Make the screen better.” | 1 | FAIL | Asked for a screenshot but also supplied a generic improvement checklist before screen, task, and target runtime were identified. https://chatgpt.com/c/6ae07fed-a8f0-83eb-9a04-13f6cc675e69 |
| ID-ACCESSIBILITY-SITE-v56 | Billing permission and unavailable-data edge | 1 | PASS | Distinguished permission denial from confirmed empty, request error and unavailable states; gave accessible recovery guidance and desktop/mobile behavior without exposing billing data. https://chatgpt.com/c/6ae0801c-36a4-83eb-afd4-b6f34096ab53 |

The v0.1.2 checks add three behavioral failures and one pass. Iteration 06 remains active. The scoped v0.1.3 candidate addresses clarification-only gating, product-evidence boundaries and explicit failure paths; it requires a new Site identity lock and fresh behavioral retests before acceptance.
