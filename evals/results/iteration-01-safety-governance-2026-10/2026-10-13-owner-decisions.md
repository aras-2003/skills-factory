# Iteration 01 — owner decisions, concrete options
Prepared 2026-10-13. All options below are PROPOSED, not approved. Existing V14 archive and historical results remain unchanged.

## D1 — distribution and licensing (#249)
Recommendation: **D1-A, personal/proprietary toolkit for now**. This matches current private Site operation and preserves the option to choose an open-source model deliberately later.
- D1-A: explicitly document personal/proprietary distribution; no general third-party reuse grant. Keep current repository visibility and private Site audience. Do not imply this prevents GitHub platform view/fork rights. No invented license text.
- D1-B: MIT open source: permit third-party commercial use, modification and redistribution, including proprietary derivatives, with notices preserved.
- D1-C: Apache-2.0 open source: permissive reuse with express contributor patent grant, notice preservation and change notices. More detailed terms.
Approval applies only to owner-controlled original material, not third-party licenses or imported assets. After the choice, update docs/DISTRIBUTION-LICENSE-DECISION.md, README and relevant package metadata consistently. Do not grant rights to third-party material.

Sources: https://choosealicense.com/no-permission/ ; https://choosealicense.com/licenses/mit/ ; https://choosealicense.com/licenses/apache-2.0/

## D2 — private vulnerability intake (#249)
Recommendation: **D2-A, GitHub Private Vulnerability Reporting** for this existing public repository, with owner aras-2003 as intake maintainer.
- D2-A: enable native private reports, verify enabled status and reporter entry point, then make SECURITY.md name the observed channel. Do not submit a fictitious vulnerability report.
- D2-B: an owner-designated dedicated private mailbox. Owner supplies the address; verify access and routing before publishing it. No invented email or promised SLA.
Native reporting and public exploit Issue comments are different channels. Documentation alone does not prove native reporting enabled.

Source: https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository

## D3 — fresh positive-path TEST writes (#291/#303)
Recommendation: **D3-A, six tightly scoped fresh runs**, after isolated executor proves both Cloud Next and Supabase tools are callable and the exact installed candidate is recorded.
Existing campaign keys have consumed their write limits. This is a new authorization request, not reuse of historical approval.

- D3-A: approve the exact six runs below, only project dcqruvxwjahymcxpnyzh (investment-os-test), schema public, table research_events. One synthetic append per key; canonical identity/bootstrap/preflight/readback reads allowed. No production, real holdings, thesis activation or actual trades.
  - MON keys: codex-i01-mon002-final-20261013-r1, -r2, -r3 (full prefix repeated for each).
  - INV keys: codex-i01-inv002-final-20261013-r1, -r2, -r3.
  - MON fixture: provided synthetic ACTIVE threshold gross margin >=20%, confirmed fixture observation 15%, TEST_ONLY confidence, NULL instrument_id/thesis_id. One monitoring event each, no second write.
  - INV fixture: a single fictional TESTCO-A candidate; margin, valuation and XTB availability unknown; TEST_ONLY confidence, NULL instrument_id/thesis_id. One event each, followed by one same-key duplicate append attempt that must not create a second row. Denied key = each full INV key plus -denied; only read/check absence, no INSERT attempted.
  - A missing prerequisite aborts the affected run before effects; new approval never permits exceeding one inserted row/key.
- D3-B: read-only verification of existing six receipts and safe-abort paths. No new effects, but does not satisfy fresh-candidate independent positive-path append coverage; integration acceptance remains open.

## D4 — closing review capacity
Recommendation: **D4-A, explicit sole-maintainer review by owner**, if no independent human reviewer is available. Existing governance permits the same named owner/reviewer if the lack of independence is recorded.
- D4-A: owner reviews final exact-candidate report and signs the acceptance record; assistant prepares evidence and never signs on the owner's behalf.
- D4-B: name an independent reviewer who will review the same pinned candidate/evidence. This document does not invite/message anyone.

This choice is not final closing signoff and does not waive FAIL/BLOCKED criteria.

## Technical access work — no new policy decision required yet
- Main protection readback retried at 2026-10-13 18:45 Warsaw: connector still returns 403 Resource not accessible by integration; managed App excludes administration. No secret should be pasted into chat, no broad persistent token is proposed.
- Native Project readback should preferentially use an existing authorized read-capable path. Existing Actions project sync uses PROJECTS_TOKEN; source and previous successful writes do not prove today's full 90-item membership/fields/Iteration/dependency readback. Do not extract the secret or infer missing data.
- If an owner UI read is ultimately required, provide exact pages/fields/evidence to collect rather than ask for vague extra access. Protection should not be weakened to make closure easier.

## Execution correction and preserved verdict
The recovered GOV-001/MON-001 traces show no visible load_skill call for these case responses. thesis-monitor source already explicitly requires BLOCKED_CANONICAL_READ. Thus initial FAIL responses are preserved, but are not evidence that loaded thesis-monitor violated its contract.
A supplemental isolated diagnostic explicitly calls runtime_info then load_skill without sharing evaluator assertions. It is a separate harness variant, not a silent replacement of frozen initial input/grades.
The six writer cases likewise require provider/setup delivery. Their safe initial aborts are real; root-host supplemental writes cannot replace independent executor evidence.
Current frozen initial campaign verdict remains 21 PASS / 4 FAIL / 6 BLOCKED until matching evidence/re-adjudication is recorded.
