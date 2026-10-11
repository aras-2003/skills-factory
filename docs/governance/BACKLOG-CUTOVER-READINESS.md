# Backlog cutover readiness — 2026-10-09

## Current verified scope
- The 2026-10-05 source backlog contains **89 distinct IDs**, blob SHA `7ffb6f45b97be90e3e039ad493bdaaa2f2a26d0f`.
- All 89 IDs map to **exactly one** GitHub Issue in `docs/governance/backlog-legacy-issue-map.json` (rechecked with GitHub Issue search). No missing or duplicate legacy ID mappings in this source.
- 21 work items carry `review-required` and are **not ready to be implemented**; they may duplicate existing runtime/security/E2E fixes. Review individual acceptance criteria and exact PR/source/runtime evidence before resolution.
- Other 68 imports are candidate backlog records, **not evidence that existing capabilities were audited**.
- GitHub Project #1 auto-add + metadata sync was demonstrated for first 12 items through user screenshots. **Do not infer successful sync of all 89 solely from Issue creation**.

## Cutover gate (NOT SATISFIED)
1. Audit **all** files and references that act as active backlog sources, not only the 2026-10-05 file. Include older roadmap/plan/queue/AIS and issue-tracker files, identify active vs immutable test evidence/history. Do not delete evaluator fixtures, E2E baselines, test queues, receipts or architecture records.
2. Review 21 tagged Issues against current `main`, relevant PR diffs/commit SHAs and run evidence; close, link, or narrow with explicit disposition and evidence.
3. Reconcile new Issues against later main changes and duplicate domain capabilities. Reset priority only with a recorded triage decision.
4. Confirm all 89 Issue URLs, Project membership, Priority/Area/Size fields, dependency links and intended status by readback. Record counts, rejects and exceptions.
5. Replace active backlog references with GitHub Issues/Project links and retain this manifest as provenance.
6. Only after successful audit and owner approval, open a **separate cleanup PR** changing redundant backlog files or archiving them. Keep historical source in Git history, with an immutable SHA reference and no evidence loss.

## Source of truth (planned)
- GitHub Issues = actionable backlog (after cutover).
- GitHub Project #1 = portfolio status/priority/iteration views.
- Repository docs, skills and tests = technical contracts and evidence.
- Older backlog files = historical sources, never runtime PASS evidence.

**Status: ID-MAPPED, CUTOVER BLOCKED.** Migration completeness of IDs is not repository-cleanup readiness.
