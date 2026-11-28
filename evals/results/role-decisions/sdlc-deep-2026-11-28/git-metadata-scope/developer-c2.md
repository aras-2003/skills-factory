# Developer implementation phase — C2

- Role: `sf-developer-high`; actual Codex child thread. Effective model/effort values were not retained in the supplied execution report, so `UNKNOWN` here.
- Base: C1 `d87fee2d8e82609dd967efb85bde639e3aa3667d`.
- Candidate: `af0da82f912d5c6d12a7c84a824d818c02b95f4c`, tree `55cc4fdae19d0263fffaf5a5443b98547b84c2e6`.
- The shared path validator now rejects a complete `.git` component case-insensitively. Adjacent names such as `.github` and `.gitignore` remain valid. The guide and source compatibility hashes were updated.
- On a clean detached checkout at exact C2, command:
  `UV_CACHE_DIR=/private/tmp/sf-uv-cache uv run --offline --python 3.12 --with-requirements requirements-dev.lock python -m unittest tests.test_developer_scope tests.test_delegation_handoff tests.governance.test_sdlc_architecture_source_example scripts.eval.tests.test_runtime_campaign scripts.eval.tests.test_iteration_07_investing_quality_coverage`
- Exit: `0`; `Ran 115 tests in 80.332s`, `OK`.
- On that clean detached checkout, `git diff --check` exited `0`.
- An earlier run of the same suite on the in-progress dirty worktree exited `1` with 11 failures and 6 errors, including continuation/campaign recognition and historical path comparisons. The subsequent clean committed C2 run passed. Cause of the earlier discrepancy is `UNKNOWN`; it is not attributed solely to untracked evidence.
- This is implementation test evidence only; independent exact-candidate execution and review remain separate gates.
