# Public repository governance (ENG-21)

Status: **PARTIAL — owner distribution and review-capacity decisions approved; live controls remain evidence-gated**. This page describes the source governance baseline, not a verified GitHub branch-protection configuration or an independent security audit.

## Distribution and licensing decision

The repository is public, but **public visibility does not itself grant an open-source license**. No `LICENSE` file was present at the repository root at the source inspection on 2026-10-12. On 2026-10-13 the owner approved personal/proprietary distribution without a general third-party reuse grant. The approved decision is in [DISTRIBUTION-LICENSE-DECISION.md](../DISTRIBUTION-LICENSE-DECISION.md). Do not describe the original toolkit as MIT/Apache/GPL licensed. Existing third-party rights remain unaffected.

## Responsibility and review capacity

`.github/CODEOWNERS` maps the known repository owner `@aras-2003` to source, security, CI, release and eval paths. This creates a review routing signal; **it cannot manufacture independent review**. A same-author approval does not count as external validation. For sensitive changes, retain the reviewer limitation and evidence in the PR instead of asserting a mandatory reviewer was available.

## Review and release

1. Work on a separate branch and link an existing issue.
2. Run the appropriate deterministic CI gates on the **exact PR head**. Keep immutable source identities and artifacts.
3. Require explicit human review for safety, credentials, external writes, branch policy, and release/promote decisions. The owner approved explicit sole-maintainer closing review (D4-A): name @aras-2003 as owner/reviewer and record that the review is not independent. The assistant prepares evidence; final owner acceptance must be observed, not invented. This does not waive failing tests or mandatory GitHub checks.
4. Keep model or connector runtime behavior as `NOT_RUN` without real version-bound receipts. No protected-baseline or evaluator-rubric edits as a shortcut.
5. Promotion to production and any write to production data are separate authorized actions; a merge to `main` is not a deployment.

## Outstanding owner/admin gates

- License/distribution rights: **OWNER APPROVED — personal/proprietary**, no general reuse grant.
- Verify GitHub private vulnerability reporting works; otherwise establish an actual private contact route. **UNVERIFIED**.
- Read back branch protection, required checks and review requirements for `main`/`production` with sufficient GitHub permissions; do not claim them from the CODEOWNERS file. **UNVERIFIED**.
- Review capacity: **OWNER APPROVED — sole-maintainer owner review**, independent review **NOT PROVIDED**; final iteration acceptance remains pending.

Related: [ENG-21 #249](https://github.com/aras-2003/skills-factory/issues/249), [ENG-20 #248](https://github.com/aras-2003/skills-factory/issues/248).
