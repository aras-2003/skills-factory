# GitHub operating model

Status: **proposed; pending PR review and backlog cutover**.

## System of record
| Material | Home |
| --- | --- |
| Work items, defects, accepted improvements | GitHub Issues after verified cutover |
| Priority, status, portfolio and roadmap views | GitHub Projects over linked Issues |
| Architecture, specifications, ADRs, policies, test definitions | Versioned `docs/`, `skills/`, `workflows/`, `tests/` |
| E2E receipts, immutable evidence and attestation | Existing evidence paths and linked artifact/commit IDs |
| Discussions and uncommitted ideas | Discussion or research issue, not automatically a delivery commitment |
| Tutorials / quick start | README and versioned docs; Wiki or Pages only as derived/navigation surface |

## Project configuration (manual/admin API step)
Name: **Skills Factory — Product & Engineering**. Suggested status: Inbox, Discovery, Ready, In Progress, Review, Validation, Done. Priority: P0–P3. Area: Engineering, Runtime, E2E, Security, Commerce, Investing, OAF, Learning, Strategy, Other. Type: Bug, Feature, Improvement, Research, Governance, Epic. Effort: XS/S/M/L/XL. Views: Executive Overview, Engineering Board, P0 Critical, Ideas & Research, E2E & Quality, Roadmap, Release Readiness. Keep GitHub native assignee, labels, dates and links rather than duplicating them in text fields.

## Controlled backlog migration
1. Freeze **a copy** of current legacy source and record source commit, item count, identifiers and digests; do not freeze active development.
2. Compare against main, existing issues, merged/active PRs and live runtime evidence. A historical PROPOSED/IN_PROGRESS value is not a current verdict.
3. Classify each historical ID as **create, link existing, implemented with evidence, superseded, duplicate, defer**.
4. Import only unique actionable work as Issues, preserving historical ID, acceptance criteria, rationale and source references. Prefer an epic issue for work that needs decomposition.
5. Attach verified issues to Project; set status from evidence, not the legacy snapshot. Preserve mapping from old ID to Issue URL.
6. Reconcile counts and verify all links, status and dependencies. Obtain review before changing the canonical backlog declaration.
7. Keep historical `BACKLOG.json` intact as read-only provenance. Do not delete it or overwrite receipts.

## Gate definitions
- **Ready:** outcome, scope, dependencies and testable acceptance criteria are explicit.
- **Review:** diff and relevant checks are available; reviewer identified.
- **Validation:** evidence is tied to correct source revision, runtime/channel/surface and campaign.
- **Done:** acceptance criteria satisfied with links; CI/static PASS alone does not imply deployed/running PASS.
- **Release:** release artifacts, provenance and production deployment evidence verified separately.

## Wiki policy
No independent duplication of technical specs. Wiki optional; for a public repo it can be a handbook containing links to canonical docs. Prefer GitHub Pages/catalog that already exists for generated content.
