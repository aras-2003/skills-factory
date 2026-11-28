# Frozen test design — Git metadata path scopes

Issue #748 AC-D04, referencing closed #767 AC-03 without reopening it.

- Baseline source: `f8f097175ba7c65e59b93230b5899f675b709151`
- Baseline tree: `e0770fb830fa35945d2008bb9b702dfc0d4d633d`; this is the tree of canonical main `0d99aa375ca85a096404239ddefb20f27ffbb707`.
- Architecture impact: A1 trust boundary / EXTEND.
- Test Designer: `sf-test-designer`, requested `gpt-6.1-terra` / medium; host-visible model `gpt-6.1-terra`; effective effort and automatic TOML profile loading `UNKNOWN`.
- No files or tests were edited/executed by the Test Designer.

## Contract

Repository-relative source scopes may not name Git control metadata. Reject any complete path component equal to `.git` case-insensitively in read-only scopes, writable scopes, and reported changed paths. Preserve ordinary source paths whose names merely begin with `.git` or are adjacent to it. This validates declared paths only; it does not create a host filesystem sandbox or prevent Git's own authorized metadata writes.

## Frozen cases

| ID | Surface | Inputs | Expected |
| --- | --- | --- | --- |
| GITMETA-01 | `validate_repo_relative_path` | `.git`, `.git/`, `.git/config`, `src/.git`, `src/.git/`, `src/.git/config`, `.Git/`, `src/.GIT/config` | Reject each complete `.git` component before filesystem access. |
| GITMETA-02 | `validate_repo_relative_path` | `.github/`, `.github/workflows/ci.yml`, `.gitignore`, `.gitmodules`, `.gitconfig`, `src/.gitkeep`, `src/.gitfoo/config`, `src/git/.gitignore` | Accept and return the original path exactly. |
| GITMETA-03 | `serialize_input` and `read_input` | Starting from `valid_input()`, insert `.git/`, `.git/config`, `src/.Git/`, or `src/.GIT/config` independently into `readonly_paths` and `writable_paths`; use a valid, disjoint companion path and `context_budget=2400`. | Both serializer and bytes/text readback reject every variant. No error-string match is required. |
| GITMETA-04 | Handoff positive control | Round-trip valid read-only `.github/` and writable `.gitignore`; also `src/.gitkeep` and `src/.gitconfig`. | Both canonical serialized and JSON text readback preserve exact values. |
| GITMETA-05 | `verify_candidate_scope` | On the existing temporary clean Git repo, pass `.git`, `.git/`, `.git/config`, and `nested/.Git/` as grants; pass `.git/config` as a reported changed path without a grant. | Reject all invalid declarations before returning a scope status; do not write or read Git metadata. |
| GITMETA-06 | Scope positive control | On the temporary repo, commit `.gitignore` and `.github/workflows/ci.yml`; verify with exact grants or `.github/` plus `.gitignore`. | `PASS`, exact actual changed paths, no violations. |
| GITMETA-07 | Regression suites and source pins | Existing path-scope, delegation-handoff, developer-scope, compatibility continuation and governance digest checks on exact candidate. | All pass; prior path overlap, symlink/submodule and dirty-tree behavior remains unchanged. |

## Execution order

1. Developer adds the frozen regressions only and observes the expected RED on baseline before implementation.
2. Separate Test Executor verifies that RED on the exact baseline/test-only candidate and records commands, exits and clean state.
3. Developer implements the narrow lexical rule, updates coupled source pins and preserves valid sibling names.
4. Separate Test Executor runs the frozen focused suites and source-pin checks on the exact candidate; Independent Reviewer audits scope and evidence on that SHA.
5. If review finds a concrete defect, preserve the reviewed candidate and controlled handoff, rework once in the same assigned path, then rerun affected cases and reject stale candidate evidence. Do not manufacture a finding or candidate merely to claim rework.

## Boundaries and rollback

The regression does not exercise filesystem writes to `.git`; it proves rejection of a dangerous scope declaration. It does not prove host ACL, Git metadata immutability, filesystem alias handling, approval non-transfer, or production security. Keep the API shape and result semantics unchanged. If rolled back, suspend acceptance of pending Developer scopes containing a `.git` component and revalidate them from trusted task definitions; preserve historical receipts.
