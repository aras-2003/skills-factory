# ENG-16 static capability inventory — 2026-10-09

## Scope and decision

Inventory **54 skills + 16 registered runtime workflows = 70 components**.
The unregistered `workflows/skill-development/WORKFLOW.md` is outside the
registered runtime count. This PR is **source analysis only**, not a claim that
a component has been observed executing in Lab, Site, Chat or production.

The exact per-component contract and source path are in
`release/capability-contract.yaml`, with the five existing dimensions:
`network`, `filesystem`, `shell_exec`, `credentials`,
`external_actions`. Every registered component is explicitly inventoried.

## Conservative evidence policy

- An affirmative `read`/`write` or `named_classes` capability is a
  **source-implied requirement**, not observed use or a grant of permission.
- `none` is **never inferred from silence** in a SKILL.md or WORKFLOW.md.
- `unassessed` means the source does not establish a safe, exact capability
  requirement; do not equate this with `none` or unsupported runtime.
- A `write` requirement can be conditional upon a user's authorized task.
  A capability declaration is not permission to execute a write.
- All 70 entries retain `review_state: STATIC_PARTIAL` until independently
  verified. None is eligible for a runtime compatibility PASS on this basis.

## Explicit evidence cases in the source review

| Components | Source evidence | Source-implied capability |
|---|---|---|
| company-context-research | Prefer official company reports, filings and current sources | network: read |
| job-discovery | Search approved sources, employer ATS pages | network: read |
| commerce-regulatory-risk-review | Check current authoritative regulator/legislation guidance | network: read |
| market-opportunity-scan | Installed equity plugins, IR/filings, canonical record store | network: read; credentials: named_classes |
| investment-record-store | Supabase/Postgres canonical READ/WRITE with authorization boundary | network: write; credentials: named_classes; external_actions: approval_required |
| decision-journal-update | Append canonical records only after explicit user authorization | network: write; external_actions: approval_required |
| investment-opportunity-hunter | Delegated canonical research-state writes via investment-record-store | network: write; credentials: named_classes; external_actions: approval_required |
| investment-attention-triage, portfolio-state-review | Conditional delegated canonical persistence | network: write |
| investment-attention-review, investment-portfolio-observation, investment-portfolio-review | Conditional canonical persistence | network: write |
| investment-security-review, investment-theme-discovery | Canonical research/thesis/theme write through store | network: write |

Sources are linked per component by the `source` field in the contract.
**Every other dimension stays `unassessed`** until a stronger static or
runtime evidence source exists. The review makes no inference of filesystem,
shell, or credential absence from a workflow's silence.

## Validation and handoff

```bash
python scripts/capabilities/validate_contract.py --report .tmp/capability-static-report.json
python -m unittest discover -s scripts/capabilities/tests -p 'test_*.py'
```

The validator rejects missing components, mismatched source paths, unknown
capabilities and missing review-state provenance. It reports the explicit
inventory count and partial evidence count. Catalog generation must not turn
partial declarations into `DECLARED` (see the sibling ENG-16/17 review
in [PR #275](https://github.com/aras-2003/skills-factory/pull/275)).

## Separate follow-up: NOT_RUN

After merging the source contract, a separate runtime campaign must verify
actual connector availability, denied tool/credential cases, side-effect
boundaries, approvals, persistence receipts and differences between channels.
No runtime test or deployment is performed by this inventory PR.
