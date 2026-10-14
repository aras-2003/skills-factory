# Public repository governance (ENG-21)

Status: **PARTIAL — distribution and intake resolved; closing review pending**. This page describes the source governance baseline, not an independent security audit.

## Distribution and licensing decision

The owner approved **D1-A, personal/proprietary toolkit with no general third-party reuse grant**; see the [decision record](../DISTRIBUTION-LICENSE-DECISION.md). Public visibility, applicable law, GitHub platform rights and third-party licenses are unaffected. Do not describe this project as MIT/Apache/GPL licensed or invent a proprietary license text.

## Responsibility and review capacity

`.github/CODEOWNERS` maps the known repository owner `@aras-2003` to source, security, CI, release and eval paths. This creates a review routing signal; **it cannot manufacture independent review**. A same-author approval does not count as external validation. For sensitive changes, retain the reviewer limitation and evidence in the PR instead of asserting a mandatory reviewer was available.

## Review and release

1. Work on a separate branch and link an existing issue.
2. Run the appropriate deterministic CI gates on the **exact PR head**. Keep immutable source identities and artifacts.
3. Require explicit human review for safety, credentials, external writes, branch policy, and release/promote decisions. If the owner is the only maintainer, state that independent peer review is pending, not passed.
4. Keep model or connector runtime behavior as `NOT_RUN` without real version-bound receipts. No protected-baseline or evaluator-rubric edits as a shortcut.
5. Promotion to production and any write to production data are separate authorized actions; a merge to `main` is not a deployment.

## Outstanding owner/admin gates

- Distribution choice: **OWNER_APPROVED D1-A**, recorded 2026-10-14.
- Private vulnerability intake: **ENABLED, UI readback 2026-10-14**. The owner approved D2-A; the existing enabled setting needed no change. No fictitious vulnerability report was submitted.
- Branch protection: **API + UI READBACK 2026-10-14**. Both branches require PRs, current branches, required checks, prohibit force pushes/deletion and enforce rules for admins. `main`: `validate` and `domain`; `production`: additionally `promotion`. Approval count is zero and conversation resolution is not required. The connector's historical HTTP 403 is preserved; authenticated GitHub CLI API reads supplied the authoritative current configuration. See the [evidence report](../../evals/results/iteration-01-safety-governance-2026-10/2026-10-14-continuation-report.md).
- Review capacity: owner selected **D4-A, explicit sole-maintainer closing review**. Independence remains **NOT_VERIFIED**. This selects the reviewer; it does not sign the final candidate or waive failed/blocked criteria.

Related: [ENG-21 #249](https://github.com/aras-2003/skills-factory/issues/249), [ENG-20 #248](https://github.com/aras-2003/skills-factory/issues/248).
