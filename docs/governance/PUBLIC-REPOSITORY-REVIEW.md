# Public repository governance (ENG-21)

Status: **PARTIAL — maintainer decisions required**. This page describes the source governance baseline, not a verified GitHub branch-protection configuration or an independent security audit.

## Distribution and licensing decision

The repository is public, but **public visibility does not itself grant an open-source license**. No `LICENSE` file was present at the repository root at the source inspection on 2026-10-12. The owner has not authorized choosing a license in this iteration. Until a documented decision, do not describe this project as MIT/Apache/GPL licensed or assume redistribution rights. Owner decision: open source under an explicitly chosen license, reference-only access, or another policy, after reviewing third-party assets and dependencies.

## Responsibility and review capacity

`.github/CODEOWNERS` maps the known repository owner `@aras-2003` to source, security, CI, release and eval paths. This creates a review routing signal; **it cannot manufacture independent review**. A same-author approval does not count as external validation. For sensitive changes, retain the reviewer limitation and evidence in the PR instead of asserting a mandatory reviewer was available.

## Review and release

1. Work on a separate branch and link an existing issue.
2. Run the appropriate deterministic CI gates on the **exact PR head**. Keep immutable source identities and artifacts.
3. Require explicit human review for safety, credentials, external writes, branch policy, and release/promote decisions. If the owner is the only maintainer, state that independent peer review is pending, not passed.
4. Keep model or connector runtime behavior as `NOT_RUN` without real version-bound receipts. No protected-baseline or evaluator-rubric edits as a shortcut.
5. Promotion to production and any write to production data are separate authorized actions; a merge to `main` is not a deployment.

## Outstanding owner/admin gates

- Choose and approve license/distribution rights. **NOT_DECIDED**.
- Verify GitHub private vulnerability reporting works; otherwise establish an actual private contact route. **UNVERIFIED**.
- Read back branch protection, required checks and review requirements for `main`/`production` with sufficient GitHub permissions; do not claim them from the CODEOWNERS file. **UNVERIFIED**.
- Verify whether another qualified reviewer is available; until then, report independent review as **NOT_VERIFIED**.

Related: [ENG-21 #249](https://github.com/aras-2003/skills-factory/issues/249), [ENG-20 #248](https://github.com/aras-2003/skills-factory/issues/248).
