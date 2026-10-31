# Iteration 06 — interface-design Site acceptance

- State: ACTIVE
- Tracking Issue: [#483](https://github.com/aras-2003/skills-factory/issues/483)
- Replaces acceptance work only; Iteration 05 remains ABORTED and unchanged.
- Owner: Arkadiusz Kamrowski
- Reviewer: Arkadiusz Kamrowski (self-review; not independent)
- Started: 2026-10-27

## Locked scope

Verify the already merged `interface-design` behavior and fixes from #475/#478/#481 on the currently deployed Skills Factory Cloud Next Site in ordinary Chat. This is semantic verification, not new capability development. Keep #423, #474 and #480 open until evidence supports their individual closure. #424–#426 remain excluded.

The six source cases are reused unchanged from `skills/web-design/interface-design/tests/cases.yaml`; input hashes and run counts are pinned in [the acceptance matrix](../../../evals/campaigns/iteration-06-interface-design-site-2026-10/acceptance-matrix.md). Evaluator assertions remain outside executor prompts.

## Candidate and runtime lock

- Canonical source SHA: `7c0f545a054ee411bb79d7a5bc6c0c2b26a3e3b6`.
- Site deployment: version 54; provider mirror SHA `d75338ea2b3bad53142702e73f1f75d689f83394`.
- Runtime package: `1.38.369+7c0f545a054e`; payload SHA-256 `8de018e5828bd85483fe5634c021e2d97d2cebf3addf9ab73132146e5652b8a5`; Site attestation verified.
- Runtime identity receipt: `2026-10-27T08:25:45.761Z`, receipt output SHA-256 `1f8b9a759fd031946bc0ff6a399f3236421f63c3f434c616f05dd032d552bb98`.
- Applicable main checks at canonical SHA `7c0f545a…`: 19 check-runs; all required validation, domain, build and release checks succeeded. The governance project-mapping check was skipped by its path filter.
- Separate Lab-host execution is unavailable in this ordinary Chat. Site's embedded Lab artifact is not a separate Lab host. Lab is supplemental under the prospective policy in `ITERATION-DELIVERY.md`; no cross-host parity claim is made.

The pinned Site identity is verified at lock. If deployed source changes before all rows finish, stop and re-pin a new candidate before continuing.

## Required runtime matrix

All prompts execute through actual Site MCP invocations and host execution. Run each critical routing row three independent times and preserve all attempts. No retry-until-green. Load/identity receipts do not constitute behavior PASS. Use synthetic inputs only; no external reads, messages, purchases, data writes or persistence.

1. Six semantic cases: direct positive, indirect positive, report/diagram near-miss, implementation near-miss, insufficient context and accessibility/permission edge.
2. Three critical routing cases × three independent attempts: natural interface-design positive, report/diagram near-miss and implementation near-miss.
3. Shared sentinels I01-SENT-001 and I01-SENT-002, once each.
4. Two preselected unchanged-domain probes, once each: synthetic Investment Opportunity Hunter candidate screening and synthetic Commerce unit economics.
5. One identity and actual skill-invocation smoke for the pinned Site candidate.

Specific defect assertions:

- #474: the direct-positive case must not invent order IDs, order status, counts, dates, delivery estimates, capabilities or other operational/product data.
- #480: the insufficient-context prompt must ask what screen, user task and target runtime are intended; it must not infer context from this or any unrelated conversation history.
- Near-misses must retain their report/diagram or implementation goal rather than emit a design-only brief.
- Accessibility assertions must distinguish permission-unavailable data from a genuinely empty account and describe accessible mobile/desktop states without claiming implementation.

## Offline and CI gates

- Run `python scripts/eval/campaign.py validate`, `python scripts/eval/validate_isolation.py`, and the applicable focused campaign/capability tests against this exact source.
- Link exact-source `Validate skills`, `Domain integrity`, `Validate Cloud Next Site`, package and security CI evidence. These gates were green for the locked source at scope start.
- Preserve every historical Iteration 05 verdict. New evidence is recorded only in this iteration's matrix.

## Closure

Close only after every required matrix row passes on the pinned Site candidate, failed rows are corrected and re-run on a newly pinned candidate, and #423/#474/#480 are reconciled individually. Record residual risk and the explicit self-review limitation. Iteration 05's aborted record and failures are never rewritten.


## Corrective re-pin — 2026-10-31

The Site 82 behavioral probes found a direct-positive answer proposing an unprovided account-navigation route and an implementation near-miss that asked interface-design context questions. The frozen fixture now makes those failures explicit. This is corrective work for failed acceptance rows; the acceptance scope is unchanged, and the original failures remain preserved.

- Corrective PR: #527.
- Candidate `interface-design`: v0.1.5; source-file SHA-256 `bbb14b50d3bc66ef5cb91089d72851252330a8fb7e62e9d194827a459638b7f8`.
- The active campaign now includes the skill path and pins this exact content SHA. The Site canonical source revision is pending merge and publication.
- No updated-runtime PASS is claimed until the frozen cases are rerun on the exact published Site candidate.
