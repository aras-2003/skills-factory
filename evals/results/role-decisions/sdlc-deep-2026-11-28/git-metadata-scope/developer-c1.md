# Developer test-only phase — C1

- Role: `sf-developer-medium`; actual Codex child thread. Effective model/effort values were not retained in the supplied execution report, so `UNKNOWN` here.
- Base: `f8f097175ba7c65e59b93230b5899f675b709151`, tree `e0770fb830fa35945d2008bb9b702dfc0d4d633d`.
- Candidate: `d87fee2d8e82609dd967efb85bde639e3aa3667d`, tree `1410d3a038268a2442100b301619ce9e13eab75d`.
- Changed only `tests/test_developer_scope.py` and `tests/test_delegation_handoff.py`.
- Command: `UV_CACHE_DIR=/private/tmp/sf-uv-cache uv run --offline --python 3.12 --with-requirements requirements-dev.lock python -m unittest tests.test_developer_scope tests.test_delegation_handoff`
- Exit: `1`; summary `Ran 64 tests`, `FAILED (failures=21)`. Final failures were the expected `.git` complete-component acceptance cases: 8 lexical, 5 candidate-scope, 8 handoff cases. Positive sibling controls and existing cases passed.
- `git diff --check` exited 0 before the C1 commit.
- The Developer first corrected a test-only NameError in the mock assertion, then reran the focused command. This note records the final run only; no raw output file was retained.
- C1 is a test-only expected RED checkpoint, not a product acceptance result.
