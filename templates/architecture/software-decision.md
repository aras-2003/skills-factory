# Software architecture decision: <short title>

> Copy this template for an A2–A4 decision or another material contract change.
> Leave unknown facts explicitly `UNKNOWN`; this record is advisory and does not
> approve a merge, migration, release, or production action.

## Decision identity

- Issue and numbered acceptance criteria:
- Decision ID / link:
- Architecture Impact as recorded in the project:
- Status: `DRAFT | REVIEW_REQUIRED | ACCEPTED | SUPERSEDED | BLOCKED`
- Baseline source SHA (40 hex):
- Candidate source SHA (40 hex, or `NOT_CREATED`):
- Decision owner / independent reviewer:
- Related existing ADRs and contracts:

## Context and scope

- Problem and desired behavior:
- Changed paths and public interfaces:
- In-scope / out-of-scope consumers:
- Constraints, assumptions, and unknowns:

## Evidence-backed component and consumer map

| Producer / interface | Consumer | Source path and line | Contract or schema | Evidence SHA/status |
| --- | --- | --- | --- | --- |
| | | | | |

List direct and transitive consumers separately. Mark missing edges `UNKNOWN`
and broaden regression selection; an empty list is not proof of no consumers.

## Trust boundaries and operations

- Data sensitivity and trust boundaries:
- Authentication / authorization / tool permissions:
- Network, deployment, and environment constraints:
- Failure modes, partial results, and observability:
- Security negative tests and required approval owner:

## Decision

- Selected option: `REUSE | EXTEND | COMPOSE | CREATE`
- Rationale and source evidence:
- Alternatives considered and trade-offs:
- Compatibility/version behavior:

## Migration and recovery

1. Pre-change checks and compatibility requirements:
2. Ordered migration or rollout steps:
3. Post-change verification and acceptance cases:
4. Rollback steps, or forward-fix if rollback cannot safely restore state:
5. Data/state restoration limits and owner approval:

For a documentation/configuration-only change, state explicitly that no runtime
state migration occurs and identify the exact files/commit to revert.

## Verification and handoff

| Case ID | Criterion | Expected / forbidden behavior | Command or runtime action | Evidence reference | State |
| --- | --- | --- | --- | --- | --- |
| | | | | | `NOT_RUN` |

- Consumer regression selection and why:
- Independent review against the exact diff and candidate SHA:
- Stale-decision rule: any changed material contract or consumer set requires re-review.
- Unresolved risks / blockers / resumption condition:
- Explicit approvals still required:

## Decision review

- Does the decision SHA match the reviewed source and candidate?
- Does every material consumer have source-backed evidence?
- Are compatibility, security, migration, and recovery criteria resolved?
- If any answer is no or unknown, disposition remains `REVIEW_REQUIRED` or `BLOCKED`.
