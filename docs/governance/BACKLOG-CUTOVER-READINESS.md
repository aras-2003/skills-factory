# Backlog cutover readiness — 2026-10-09

## Current verified scope — 2026-10-12
- The preserved `docs/roadmap/2026-10-05/BACKLOG.json` contains **90 distinct IDs** (blob SHA `7724d6bdc86f64188b4dcf522225253b54bc564c`), including ENG-22 added on 2026-10-09; previous 89-ID report described an older blob.
- The 90 IDs map to 90 unique GitHub Issues in `docs/governance/backlog-legacy-issue-map.json`. ENG-22 was missing and is now tracked as [#335](https://github.com/aras-2003/skills-factory/issues/335), **review-required**, not implementation-ready. This is **identifier coverage**, not 90 completed overlap/security/runtime audits.
- The original 21 flagged historical IDs required overlap review; ENG-22 is a further flagged entry. Verify current label states individually rather than deriving a live count from old snapshot totals.
- Project #1 auto-add and metadata synchronization were previously demonstrated on a bounded set, **not read back for all 90**. The connected GitHub issue API cannot read native Project V2 item fields or Iteration values in this session. Issue markers and queued status-sync workflows are requests to change the Project, not evidence they succeeded.
- The repository source and runtime evidence must be evaluated at their exact revisions. This map is not a release, merge, runtime or cutover receipt.

## Cutover gate (NOT SATISFIED)
1. Audit **all** files and references that act as active backlog sources, not only the 2026-10-05 file. Include older roadmap/plan/queue/AIS and issue-tracker files, identify active vs immutable test evidence/history. Do not delete evaluator fixtures, E2E baselines, test queues, receipts or architecture records.
2. Review 21 tagged Issues against current `main`, relevant PR diffs/commit SHAs and run evidence; close, link, or narrow with explicit disposition and evidence.
3. Reconcile new Issues against later main changes and duplicate domain capabilities. Reset priority only with a recorded triage decision.
4. Confirm all 90 Issue URLs, Project membership, Priority/Area/Size fields, dependency links and intended status by readback. Record counts, rejects and exceptions.
5. Replace active backlog references with GitHub Issues/Project links and retain this manifest as provenance.
6. Only after successful audit and owner approval, open a **separate cleanup PR** changing redundant backlog files or archiving them. Keep historical source in Git history, with an immutable SHA reference and no evidence loss.

## Source of truth (planned)
- GitHub Issues = actionable backlog (after cutover).
- GitHub Project #1 = portfolio status/priority/iteration views.
- Repository docs, skills and tests = technical contracts and evidence.
- Older backlog files = historical sources, never runtime PASS evidence.

**Status: ID-MAPPED, CUTOVER BLOCKED.** Migration completeness of IDs is not repository-cleanup readiness.

## Native Iteration readback — 2026-10-14

Project #1, view “By Iteration”, showed **01 | Safety + governance**, dated **2026-10-09 through 2026-10-22**, with ten native items: #160, #233, #234, #245, #246, #248, #249, #258, #291 and #303. Priority, Size, Area and Status were visible for all ten; #233 was Done, #160/#258 In progress, and the other seven Validation. This is a bounded native readback, not a claim of 90/90 membership or dependencies.

The source-bound legacy-map validator again passed with 90 distinct historical IDs mapped to 90 unique Issues. The initial full Project read lacked `read:project`; the owner subsequently approved adding only that scope and completed GitHub authentication. The resulting native API read contains 140 Project items and confirms **90/90 mapped Issues present exactly once**. All mapped items expose Priority, Area and Status; ENG-22/#335 has no Size or Iteration. Those fields were not invented for an untriaged, review-required item.

Native `blockedBy`, `blocking`, `subIssues` and `parent` reads completed for all 90 Issues without pagination or missing nodes: every relationship was empty. The historical source contains **153 proposed dependency edges**. These are not automatically current intended dependencies; their disposition still needs reconciliation. Membership is verified, but field completeness, dependency reconciliation, overlap review and owner cutover remain open. See the [public continuation summary](../../evals/results/iteration-01-safety-governance-2026-10/2026-10-14-continuation-report.md); native readback and dependency receipts are retained in the owner's local private evidence package.
