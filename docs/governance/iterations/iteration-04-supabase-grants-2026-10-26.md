# Iteration 04 — Supabase migration grants and isolated replay

Status: ACTIVE (scope locked before implementation)

## Lock

- Date: 2026-10-26
- Baseline `main`: `87a10f72c62db87910cc4e9d173489320aa67635`
- Tracking issue: [#387](https://github.com/aras-2003/skills-factory/issues/387)
- Outcome: make Investment OS database migrations reproducible from repository source and keep private data inaccessible through `anon` / `authenticated` while preserving the server-side `service_role` path.
- Owner: Arkadiusz Kamrowski.
- Implementer: Codex, working under owner direction. Reviewer: owner; this is not independent review.
- Required runtime: isolated Supabase project `investment-os-test` (`dcqruvxwjahymcxpnyzh`), pinned to the final migration candidate. Production is out of scope for iteration execution.
- Prior iteration records: Iterations 01, 02, and 03 are terminal on this baseline. No other active record was found.

## Fixed scope

Only #387 is committed in this increment. The open routing, campaign, UX, and backlog issues without a confirmed native Project Iteration remain outside this lock and must be reconciled in later, sequential records. This record does not claim that the native Project Iteration field was updated.

Read the 19 applied production migration statements only to reconstruct migration source. Do not copy DML, operational/seed data, or secrets. Do not apply or alter production migrations. Do not change production defaults or publish a release from this iteration.

## Acceptance criteria and test map

| Criterion | Acceptance | Planned evidence |
| --- | --- | --- |
| AC-01 | All migration source needed to reproduce the current schema is checked in, chronological, free of copied DML and credentials, and passes an empty-database replay. | `SF387-MIGRATION-REPLAY` |
| AC-02 | Each newly created table, view, sequence, and callable function has explicit least-privilege grants in the creating migration; private Investment OS objects are denied to `PUBLIC`, `anon`, and `authenticated`. | `SF387-OBJECT-GRANTS`, `SF387-ROLE-DENY` |
| AC-03 | RLS is enabled where required; policies match the private server-side access model; views do not bypass RLS or expose data through the Data API. | `SF387-RLS`, `SF387-VIEWS` |
| AC-04 | Default privileges for objects created by the migration owner do not expose tables, sequences, or functions to public client roles; explicit service-role access remains effective. | `SF387-DEFAULT-ACL`, `SF387-SERVICE-ROLE` |
| AC-05 | CI runs deterministic migration lint and clean replay plus positive and negative role/API checks on the exact PR SHA. | `SF387-CI` |
| AC-06 | The isolated test project completes replay and runtime authorization checks; advisor findings are reviewed; rollback and restore procedure is documented. | `SF387-TEST-PROJECT`, `SF387-ADVISOR`, `SF387-ROLLBACK` |

## Initial evidence

- Production migration ledger read-only snapshot: 19 migrations, latest `20261011220551` (`ppk_fund_allocation_observations`). Their SQL source is not present on baseline `main`.
- `investment-os-test` was observed `ACTIVE_HEALTHY`, PostgreSQL 17.11.0.003, with 26 public tables and 14 views; tables had RLS enabled. Effective privileges showed no table or view SELECT for `anon` / `authenticated`, and `service_role` could SELECT all 26 tables and 14 views. This is a pre-change observation, not acceptance evidence.
- Security advisor reports `RLS Enabled No Policy` informational findings for private tables. This matches deny-all for client roles only if service-role and server-side access are verified; the final review must confirm every table and view.
- The test project already contains a `secure_public_data_api_defaults` migration not present in the production ledger or repository. Its source will be treated as reference evidence, reviewed, and reconstructed in the repo; it is not proof that the repository can replay the production schema.
- No production data rows, SQL migration DML, or credentials are part of the source reconstruction.

## Required surfaces and execution state

| Surface | Requirement | State |
| --- | --- | --- |
| PR/CI | Static migration lint and clean replay, exact SHA | NOT_RUN |
| `investment-os-test` | Isolated migration replay and SQL role checks | NOT_RUN |
| Test-project Data API | Deny client reads/writes; verify authorized server path without disclosing keys | NOT_RUN |
| Production | No migration execution in this increment | N/A — excluded by scope |

## Closure gate

Keep #387 open in Verification until each required row passes on the final candidate and the test-project receipt is retained. If the authorized server-side API path cannot be exercised without accessing an unavailable credential, record that exact limitation and leave that acceptance row open. Production deployment is not required for closure.
