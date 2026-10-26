# Development and release model

## Goal

Keep `main` current and useful for continuous development while `production` remains a reproducible personal runtime snapshot. Avoid long-lived stacked PR chains and stale integration branches.

## Branch model

- `main` is the stable integration branch. Every change enters through a pull request and required CI checks; direct pushes and force pushes are disabled.
- `production` is the explicitly promoted snapshot. It also accepts changes only through a pull request and required checks; no workflow promotes or merges it automatically.
- Work normally starts on short-lived branches. A pull request must pass `Validate skills` and `Domain integrity` before it can merge into `main`.
- Do not stack long-lived PRs for sequential phases when one consolidated change can be integrated and validated on `main`.
- Once a stacked/temporary branch is fully represented on `main`, close its PR as superseded.

## Personal-beta production rule

This repository is primarily a personal system. A temporary personal-beta exception may continue use only for a component already declared production, at the exact recorded version, while runtime evidence is pending. It does not authorize a new production promotion, a changed component/version, expanded scope or a wider audience. A new promotion must pass its current mandatory release gates for the exact artifact and channel. No exception covers a known unresolved high-severity failure. For an existing-component continuation, all of the following are true:

1. static contracts and repository validators pass;
2. package builds and artifact validation pass;
3. relevant deterministic/unit tests pass;
4. executor inputs remain isolated from evaluator rubrics;
5. runtime evidence gaps are recorded as `NOT_RUN` / `pending`;
6. no unresolved known high-severity failure exists;
7. the readiness exception has an owner and short expiry.

Personal-beta production is not the same as verified runtime PASS.

## Change flow

For normal incremental work:

1. create a short-lived branch from `main` and open a PR;
2. merge only after `Validate skills` and `Domain integrity` pass;
3. `.github/workflows/release-lab-plugin.yml` builds and validates the Lab artifact from the exact merged `main` commit, bumps the Lab patch version, uploads the immutable candidate and opens a Marketplace package PR from that same source revision; the PR contains the generated Lab package and release receipt, and is subject to the normal branch protections;
4. review and merge the generated Marketplace package PR, then install/run that exact Lab candidate and retain its runtime receipt;
5. fix blockers rather than weakening validators;
6. production is released only after an explicit user request. Prepare a promotion PR containing production packages built from the exact Lab `source_revision`; include `release/promotion-evidence.json` bound to the Lab release id and digest;
7. `.github/workflows/release-production-plugin.yml` validates the PR, all generated package manifests, the exact Lab-to-production source chain, and the runtime receipt. It never pushes or merges.

The Lab packaging workflow never writes directly to `main`, merges the Marketplace PR, or publishes the Site. The promotion validator rejects mismatched revisions, missing runtime evidence, missing package digests, or missing run identity. Production PR merge is a human-triggered release action, not an automatic consequence of a `main` merge.

The active model-output campaign pins changes under `skills/`, `workflows/` and `release/package.yaml`. Changes under `runtime/mcp/` or `runtime/contracts/` require deterministic MCP contract tests; Cloud Next adapter changes additionally require Site typecheck, lint and build gates. If such a runtime change alters model-visible instructions or outcomes, add it to a scoped behavior campaign before claiming runtime compatibility. Site-only UI changes do not by themselves invalidate a host-model campaign for skill behavior. The CI workflow builds Lab and production artifacts once and reuses them for runtime handoffs; the separately required Site workflow builds Lab independently.

## Evidence discipline

- Offline/static checks are never described as runtime PASS.
- Historical PASS/FAIL remains bound to its original component version and source revision.
- A pending-evidence exception is limited to an already-declared production component and exact version, and records the gap, limitation, owner and expiry. It never authorizes a new promotion or materially changed version.
- Failures discovered in real use should become regression fixtures before the next meaningful release.

## Promotion cadence

Promote when there is a useful coherent increment, not for every edit. The expected steady state is:
- few or zero open PRs;
- current `main`;
- an immutable Lab candidate tied to one `main` source revision;
- one known `production` snapshot;
- explicit Lab runtime evidence for every production promotion;
- continuous learning from real use.


## Iteration delivery

Follow [Iteration delivery and quality gates](governance/ITERATION-DELIVERY.md) for frozen scope, the single active increment, exact-candidate test coverage, corrective work, failure severity and closure before starting the next iteration. Main integration after offline checks remains separate from runtime acceptance and production promotion.
