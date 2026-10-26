# Iteration 04 — Supabase grants acceptance matrix

Candidate baseline: `87a10f72c62db87910cc4e9d173489320aa67635` (lock commit pending).

| Row ID | Issue / criterion | Layer + case | Required surface | Candidate | State | Verdict | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SF387-MIGRATION-REPLAY | #387 AC-01 | Empty database replay of all checked-in migrations | CI/local disposable PostgreSQL | TBD | NOT_RUN | none | pending |
| SF387-OBJECT-GRANTS | #387 AC-02 | Every created object gets explicit role grants in its creation migration | CI/static | TBD | NOT_RUN | none | pending |
| SF387-ROLE-DENY | #387 AC-02 | anon/authenticated cannot SELECT, INSERT, UPDATE, DELETE private data | CI + test DB/Data API | TBD | NOT_RUN | none | pending |
| SF387-RLS | #387 AC-03 | RLS enabled on private public-schema tables; no unintended policy grant | CI + test DB | TBD | NOT_RUN | none | pending |
| SF387-VIEWS | #387 AC-03 | Views use security_invoker or remain inaccessible to client roles | CI + test DB | TBD | NOT_RUN | none | pending |
| SF387-DEFAULT-ACL | #387 AC-04 | Future tables, sequences, and functions are denied to PUBLIC/anon/authenticated by default | CI + test DB | TBD | NOT_RUN | none | pending |
| SF387-SERVICE-ROLE | #387 AC-04 | Server-only role retains the explicit access required by actual consumers | CI + test DB/API | TBD | NOT_RUN | none | pending |
| SF387-CI | #387 AC-05 | Required repository checks pass at exact PR SHA | GitHub Actions | TBD | NOT_RUN | none | pending |
| SF387-TEST-PROJECT | #387 AC-06 | Isolated project migration replay and authorization checks pass | `investment-os-test` | TBD | NOT_RUN | none | pending |
| SF387-ADVISOR | #387 AC-06 | Supabase security advisor findings reviewed and resolved or dispositioned | `investment-os-test` | TBD | NOT_RUN | none | pending |
| SF387-ROLLBACK | #387 AC-06 | Restore/rollback instructions validated without affecting production | Documentation + test project | TBD | NOT_RUN | none | pending |

Tested schema contains no private user rows in this matrix. No credentials or production data may be written into fixtures, artifacts, logs, or receipts.
