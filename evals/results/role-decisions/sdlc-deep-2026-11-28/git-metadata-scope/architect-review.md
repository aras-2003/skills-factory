# Architect review — Git metadata path scopes

- Decision: **A1 / EXTEND · REVIEW_REQUIRED**.
- Baseline: local source SHA `f8f097175ba7c65e59b93230b5899f675b709151`, tree `e0770fb830fa35945d2008bb9b702dfc0d4d633d`; tree matches canonical main `0d99aa375ca85a096404239ddefb20f27ffbb707`.
- Requested profile: `sf-architect`, `gpt-6.2-sol` / high.
- Host-visible model: `gpt-6.2-sol` (reported by the Architect child); effective effort and automatic TOML profile loading remain `UNKNOWN`.
- Review was read-only; tests were not run by the Architect.

## Finding and limits

`validate_repo_relative_path` accepts `.git` as a complete path component. `delegation_handoff.validate_input` uses that shared lexical validator, so a task can declare a Git-metadata path as read-only or writable. `verify_candidate_scope` can also return `PASS` for a clean candidate when given that explicit grant because Git status and the committed diff do not cover `.git` contents.

This is a **scope declaration validation defect**. It does not prove that a committed source change bypassed the diff verifier, and it does not prove that host access controls allowed a child to modify `.git`. The verifier is a post-execution consistency check; it is not an ACL. Git's own authorized operations may update metadata as usual.

## Recommended bounded fix

Reject a complete `.git` component case-insensitively in the shared repository-relative validator. Apply this rule to input path scopes and reported changed paths. Preserve ordinary source names such as `.github/`, `.gitignore`, `.gitmodules`, `.gitconfig`, `.gitkeep`, and `.gitfoo`; match the full component rather than a prefix. Do not attempt filesystem alias detection or broaden this change into a host sandbox.

Cover the shared validator, handoff serialization/readback, and candidate-scope preconditions with harmless path-string tests. No write to actual Git metadata is needed. Preserve v1 fields and signatures. Keep the implementation, tests, existing source-continuation pins and governance digest checks synchronized.

## Consumers and compatibility

Confirmed consumers are `delegation_handoff.validate_input`, `developer_scope.verify_candidate_scope`, `tests/test_delegation_handoff.py`, `tests/test_developer_scope.py`, the existing continuation manifest, and the governance source-digest test. Existing architecture decision `docs/architecture/decisions/2026-11-handoff-path-scopes.md` documents the shared path grammar. External callers are unknown.

Track the fix under open #748 AC-D04 and reference #767 AC-03 without reopening the closed #767 issue. Rollback should suspend dispatch of pending scopes that explicitly include a `.git` component until they are regenerated from trusted task definitions; preserve historical receipts.
