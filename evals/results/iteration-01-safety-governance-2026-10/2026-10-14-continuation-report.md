# Iteration 01 — public validation summary

Date: 2026-10-14. **NOT ACCEPTED; iteration remains open.** This supplements PR #344; the original 21 PASS / 4 FAIL / 6 BLOCKED verdict remains unchanged.

## Disclosure boundary

This is an aggregate public summary. Private TEST configuration, SQL payloads, database identifiers, session URLs, response captures and native Project receipts are retained in a local evidence package for the owner. They are not included in this PR. Automated approval review rejected the initial push containing that private payload; this independent branch starts from the original source baseline and contains no private-evidence commit in its ancestry.

## Source validation

Behavior source: `f72e27af7c4dcd35e34170162281cb84c5aa9653`.

**352 source tests passed** using Python 3.12.14 and hash-pinned `requirements-dev.lock`: evaluation 84, package 63, security 28, capabilities 16, legacy map 8, validator 63, engineering 17, output 27, readiness 11, release 6, roadmap 5, Commerce 12, Project metadata 12. The accompanying source-test JSON binds each suite log by SHA-256.

Static validation, immutable Actions references, zero-finding skill scan, capability schema, 90-ID map, evaluator isolation, 42-case R20 definition/evidence integrity, readiness registry and 15-case Iteration 1 handoff passed. Existing nonblocking test-definition warnings remain. Capability schema validity is not proof of observed capabilities or runtime acceptance. Final documentation validation and diff checks passed.

## Governance observations

Approved D1-A (personal/proprietary toolkit, no general third-party reuse grant), D2-A (private vulnerability reporting) and D4-A (sole-maintainer final review) are recorded in documentation. Private intake is enabled. Authoritative admin reads confirmed PR/check protections for both main and production, with administrator enforcement and prohibited force pushes/deletions. No protection settings were changed. Approval count is zero; reviewer selection is not final signoff or independent review.

After explicit owner approval, only `read:project` was added to GitHub CLI access. Native readback confirms all 90 mapped Issues present exactly once, matching CLOSED/OPEN and Done/non-Done states. ENG-22/#335 has no Size or Iteration. Native dependency/hierarchy relations were empty across the 90 Issues; the historical source contains 153 proposed dependency edges. Their current-intent disposition remains open. No Project state was changed.

Exact source history resolves the 89→90 transition: commit `1c42595221748f14b24e4799d51b8fa7ededc29b`, parent `b49b61e367e3292e015e48d963b57cae94c79458`, changes blob `7ffb6f45b97be90e3e039ad493bdaaa2f2a26d0f` to `7724d6bdc86f64188b4dcf522225253b54bc564c`, adding ENG-22 and removing nothing. This is an exact set comparison, not inference from cardinality or runtime acceptance.

## Runtime/integration observations

Installed Site/Lab identity was independently checked before tests. This documentation PR does not change the deployed candidate.

- Fresh GOV-001 response distinguishes counts from set membership but omits the required exact-source-revision request: **FAIL** under the frozen assertion.
- Fresh MON-001 response preserves unverified evidence and NOT_WRITTEN, but lacks the explicit required BLOCKED_CANONICAL_READ state: **FAIL** under the existing explicit-state interpretation.
- Six independent controlled TEST setup/execution attempts yielded **five successful persistence paths and one BLOCKED preflight**. All three INV repetitions reported actual same-key duplicate attempts inserting zero and denied-key absence. Independent final readback confirmed five synthetic rows, no duplicate rows and no denied-key rows.
- The blocked MON repetition reported safety-layer rejection of canonical configuration SELECT and stopped without a write. Its raw rejection reason was not exposed. Root-host reads are not substituted for its independent preflight.

Controlled integration variants embed unchanged case text together with tester setup and conditional authorization; they are not strict unchanged-input campaign PASS. Full hidden tool payloads/model identity are unavailable. Persistence readback does not prove every workflow invocation, production readiness or database-level refusal enforcement. Initial safe aborts are preserved; consumed keys cannot be written again.

## Remaining acceptance gates

1. Resolve GOV-001/MON-001 behavior and rerun the required matrix on a pinned candidate with auditable execution evidence.
2. Resolve the MON preflight block and complete strict positive-path/trace requirements without reusing consumed keys; any additional fresh-key allocation needs explicit authorization.
3. Complete ENG-22 field triage, dependency/current-intent reconciliation, exhaustive overlap/source dispositions and historical AIS/RT exact-version linkage.
4. Obtain the owner's final exact-candidate signoff after mandatory evidence passes.

No issue/iteration closure, main/production merge, Site publication or production data write is claimed. Private evidence remains available to the owner locally.
