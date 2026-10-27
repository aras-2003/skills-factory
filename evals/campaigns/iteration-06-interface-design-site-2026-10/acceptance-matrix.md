# Iteration 06 Site acceptance matrix — interface-design

Status: active; candidate v54 is tested, and the sole failing case has a fix in progress.

## Candidate identity

- Canonical Skills Factory main: `7c0f545a054ee411bb79d7a5bc6c0c2b26a3e3b6`.
- Deployed Site mirror: `d75338ea2b3bad53142702e73f1f75d689f83394` (Site v54).
- Attestation: verified; channel `site`; contract `site-mcp-v2`.
- Embedded Lab: `1.38.369+7c0f545a054e`; payload SHA-256 `8de018e5828bd85483fe5634c021e2d97d2cebf3addf9ab73132146e5652b8a5`.
- Site runtime receipt: `runtime_info` at `2026-10-27T09:04:48.075Z`, output SHA-256 `1f8b9a759fd031946bc0ff6a399f3236421f63c3f434c616f05dd032d552bb98`.
- All behavioral cases ran in ordinary Chat with the `Skills Factory Cloud Next` app explicitly selected. The transcript URLs are the retained evidence. Chat does not expose per-case MCP receipt IDs or cryptographic input/output digests; none are fabricated here.
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
| ID-CLARIFY-SITE-RETEST | Insufficient-context request after clarification-gate fix | 1 | NOT_RUN | Run only on the newly deployed candidate; record a fresh transcript. |
| ID-DIRECT-SITE-RETEST | Fully specified direct-positive control after clarification-gate fix | 1 | NOT_RUN | Run on the same newly deployed candidate to guard against over-blocking. |

## Totals

For the locked v54 execution set: 16 PASS, 1 FAIL across 17 planned executions. An additional diagnostic reproduction also failed (not counted among the 17). Two post-fix retests remain pending and will use a newly pinned candidate. Historical Iteration 05 failures remain unchanged.

## Offline checks of the v0.1.1 candidate

| Check | Verdict / evidence |
| --- | --- |
| `scripts/validate/validate_all.py` | PASS; catalog 65 unique skills; investing architecture validation passed. Existing unrelated MEDIUM/LOW advisories remain. |
| `scripts/eval/campaign.py validate` | PASS; 42 core cases resolve after the new Iteration 06 candidate is hash-pinned and isolated from frozen R20. |
| `scripts/eval/validate_isolation.py` | PASS. |
| `scripts.eval.tests.test_runtime_campaign` + `scripts.capabilities.tests.test_contract` | PASS; 31 tests. |
| `git diff --check` | PASS. |
