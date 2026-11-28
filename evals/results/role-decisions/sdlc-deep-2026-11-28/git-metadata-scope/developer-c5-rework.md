# Developer controlled rework — C5

- Input review: C4 review `review-c4.md`, finding LOW, frozen GITMETA-03 lacked invalid byte-input rejection coverage.
- Rework candidate: `60f5a31f77e8037ffc6de292843d49d9779f532b`, tree `ec77842230374a2ddb0496fa98cdb457837c5fbc`.
- Changed paths: `tests/test_delegation_handoff.py`, `tests/governance/test_sdlc_architecture_source_example.py`, and the continuation YAML source digest pins. No production source changed.
- The shared negative-input test helper now checks `serialize_input`, byte `read_input`, and string `read_input`; every GITMETA-03 invalid path goes through all three assertions.
- Focused GITMETA-03: `1 test`, `OK`, exit `0`.
- Broad clean detached C5 command:
  `UV_CACHE_DIR=/private/tmp/sf-uv-cache uv run --offline --python 3.12 --with-requirements requirements-dev.lock python -m unittest tests.test_developer_scope tests.test_delegation_handoff tests.governance.test_sdlc_architecture_source_example scripts.eval.tests.test_runtime_campaign scripts.eval.tests.test_iteration_07_investing_quality_coverage`
- Exit `0`; `Ran 115 tests in 80.982s`, `OK`; checkout clean before and after.
- `git diff --check` exit `0`.
- No meaningful regression RED applies: the change covers a missing assertion, while existing shared decoding already rejects invalid byte scopes. C4 review/execution evidence are marked stale for C5. Independent C5 review remains outstanding.
- An earlier broad run on the dirty worktree exited `1` with 7 failures/6 errors in campaign pinned-path behavior. Cause is unknown and is not attributed solely to untracked files; clean detached C5 rerun passed.
