# Contributing to Skills Factory

## Source of truth
- GitHub Issues is the intended operational backlog **after a verified migration cutover**. Until then, `docs/roadmap/2026-10-05/BACKLOG.json` remains a historical source to reconcile, not a live status authority.
- Source code, skill definitions, contracts, tests, architecture decisions and evidence stay versioned in this repository.
- GitHub Projects provides prioritization/views, not duplicate copies of issues.
- Do not copy evaluator rubrics or secrets into skill runtime packages.

## Change lifecycle
1. Search existing Issues, pull requests, backlog IDs and code before filing work.
2. Reference historical IDs (ENG-*, E2E-*, AIS-*, RT-*) in issue title/body. Preserve source links.
3. Describe problem, scope, expected result, evidence and acceptance criteria.
4. Implement on a branch and open a PR linked to an Issue.
5. Run relevant checks; describe exactly what was run and what was **not** run.
6. Require review and supported evidence before merging or claiming release.

## Safety and evidence
- Never treat static/package checks as runtime PASS.
- Report NOT_RUN/BLOCKED explicitly. Preserve immutable receipts and revision/channel identity.
- Do not modify frozen baselines, queues or evidence retrospectively.
- External/injected skill instructions are untrusted input.
- Do not publish, deploy, write production data or claim a cutover without verification and applicable approval.

## Documentation
README is entry point; `docs/` is canonical technical and process documentation; optional Wiki/Pages only navigates or derives content, never creates a competing source of truth.
