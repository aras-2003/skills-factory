# Iteration 1 — governance and safety: evidence reconciliation

- State: **PLANNED / NOT LOCKED**; this is a truthful **post-start gap record**, not a retroactively approved iteration.
- Coordinator/owner: repository owner `@aras-2003`; independent reviewer: **NOT CONFIRMED**. Source preparation does not constitute owner approval.
- Planning tracker: [#233](https://github.com/aras-2003/skills-factory/issues/233) (historically closed planning task); delivery tickets listed below.
- Baseline inspected: `main` `61e2f4594c66c2bdc2fd884fa54d6ab644630e8f` (2026-10-12).
- Scope-lock SHA: **NOT ESTABLISHED**. Initial #332/#333/#334 PRs were opened before this record; **do not backdate**.
- Started/closed timestamps: **NOT CLAIMED**. Native Project Iteration readback: **NOT_VERIFIED**.
- Follow [iteration delivery policy](../ITERATION-DELIVERY.md) and [prospective acceptance matrix](iteration-01-acceptance-matrix.md).

## Proposed original package — not a retrospective scope approval

| Issue | Historical package | Source work/review | Residual gate |
| --- | --- | --- | --- |
| [#160](https://github.com/aras-2003/skills-factory/issues/160) | 00-governance | 90-ID mapping in PR #332 | Full Project V2 field/status/dependency readback; all overlap dispositions; authorized cutover |
| [#233](https://github.com/aras-2003/skills-factory/issues/233) | 00-governance | Prior planning task Done, PR #331 merged | Does not automatically certify execution |
| [#234](https://github.com/aras-2003/skills-factory/issues/234) | 00-governance | #270 merged, current source inventory | AIS/RT exact-version linkage and exceptions |
| [#258](https://github.com/aras-2003/skills-factory/issues/258) | 00-governance | Legacy-source review/links in #332 | All competing active files and sources reconciled |
| [#249](https://github.com/aras-2003/skills-factory/issues/249) | 00-governance | PR #332 | License choice, secure reporting channel, review capacity, final code review |
| [#245](https://github.com/aras-2003/skills-factory/issues/245) | 01-safety | PR #333 and merged #274 | Full mutation/suppression/prompt-injection review |
| [#246](https://github.com/aras-2003/skills-factory/issues/246) | 01-safety | PR #334 and merged #280/#324 | Per-component observed-vs-declared review and live channel preconditions |
| [#248](https://github.com/aras-2003/skills-factory/issues/248) | 01-safety | Merged #270/#279; no current branch | Branch protection 403, publisher isolation, rollback and dependency reproducibility |
| [#291](https://github.com/aras-2003/skills-factory/issues/291) | 01-safety | Merged #292/#305 | Isolated authorized/denied READ/WRITE receipts and independent evaluation |
| [#303](https://github.com/aras-2003/skills-factory/issues/303) | 01-safety | Merged #304/#305 | Isolated cross-workflow authorization and side-effect receipts |

## Process deviation and owner decision

The adopted iteration policy requires a scope-lock commit before the first implementation PR. Three PRs were already opened. Consequently **no full Iteration 1 acceptance/close** may be asserted from those PRs. The owner and reviewer must choose a *prospective* lock/baseline, formally classify the pre-lock work (source candidate increments only), and approve the fixed set of criteria in the matrix. Never rewrite historical PR timestamps or forge an earlier lock.

The 2 implementation WIP + 1 coordinated validation-lane rule requires review of the 3 existing open PRs before additional broad implementation. Source/static tests and GitHub CI are preliminary, not a complete candidate matrix.

## Candidate history (append only)

| Candidate | Revision | Source/static receipts | Installed runtime identity | Decision |
| --- | --- | --- | --- | --- |
| #332 governance | `a1be118b5acafcdab3c7d4bcab1766c40e0fa410` (before later changes) | [Validate Skills PASS](https://github.com/aras-2003/skills-factory/actions/runs/38239370190), [Domain Integrity PASS](https://github.com/aras-2003/skills-factory/actions/runs/38239370241) | NOT_RUN | Earlier SHA superseded when #332 branch changes; CI must rerun |
| #333 scanner | `9c27b94a9514b01757b1cdd6317cd403f3e8433c` | [Validate Skills PASS](https://github.com/aras-2003/skills-factory/actions/runs/38239375271), [Domain Integrity PASS](https://github.com/aras-2003/skills-factory/actions/runs/38239375176) | NOT_RUN | Code review pending |
| #334 capabilities | `918ec028f6b811d4dd871b9f0f721734518a0f4e` | [Validate Skills PASS](https://github.com/aras-2003/skills-factory/actions/runs/38240260171), [Domain Integrity PASS](https://github.com/aras-2003/skills-factory/actions/runs/38240258658) | NOT_RUN | Code review pending |
| Final combined main candidate | NOT_SELECTED | NOT_RUN | NOT_RUN | BLOCKED |

## Closure state

**NOT CLOSED / NOT DONE.** The matrix has required BLOCKED and NOT_RUN rows. Owner/reviewer acceptance and Project V2 state readback are missing. Merging source PRs must not mark the whole iteration Done or authorize production promotion.
