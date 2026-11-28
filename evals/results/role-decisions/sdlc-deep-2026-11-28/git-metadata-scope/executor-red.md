# Independent Test Executor — expected RED on C1

- Candidate: `d87fee2d8e82609dd967efb85bde639e3aa3667d`
- Candidate tree: `1410d3a038268a2442100b301619ce9e13eab75d`
- Executor role: `sf-test-executor`; separate child thread; host-visible effective model/effort are not retained in the supplied result, so `UNKNOWN`.
- Checkout: separate clean worktree `/private/tmp/sdlc-gitmeta-red-executor`; exact candidate SHA/tree verified; clean before and after.
- Command: `UV_CACHE_DIR=/private/tmp/sf-uv-cache uv run --offline --python 3.12 --with-requirements requirements-dev.lock python -m unittest tests.test_developer_scope tests.test_delegation_handoff`
- Exit: `1`; summary: `Ran 64 tests`, `FAILED (failures=21)`.
- Scope: GITMETA-01/02/03/04/05/06. GITMETA-07 is intentionally not run in the test-only RED stage.
- Classification: expected RED. The 21 failures are all invalid complete `.git` component values accepted by the current path validator (8 lexical variants, 5 candidate-scope grant/reported-path cases, 8 handoff field/path cases). Positive sibling-name controls and pre-existing baseline cases passed.
- Raw stdout was not saved by the read-only Executor. This record preserves the Executor's exact command, exit, test count, failure classification, scope, and clean-state report; it does not claim a raw log artifact.
- Limits: this is a deterministic helper-level regression, not a host ACL, sandbox, Git metadata write-protection, approval non-transfer, or production-security result.
