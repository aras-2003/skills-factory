# Handoff path-scope validation decision

## Decision identity

- Linked criteria: #767 AC-03; #766 AC-02/03/04/05. This decision covers only path-scope validation and does not claim either Issue is complete.
- Decision ID: `SF-ADR-2026-11-HANDOFF-PATHS`.
- Architecture Impact: A2 (shared handoff contract; the native Project field was not independently read in this task).
- Status: `ACCEPTED` for implementation design; this does not approve merge or release.
- Baseline source SHA: `c414980c6cb7dbf667ea11b62f05a1de279b56bc`.
- Candidate source SHA: recorded by the PR head; this decision file is included in that candidate and cannot contain its own commit SHA.
- Decision owner: Coordinator. Architecture advice: `sf-architect`; implementation review: separate `sf-independent-reviewer`.
- Related contract: `scripts/engineering/delegation_handoff.py` input v1 and `scripts/engineering/developer_scope.py`.

## Context and scope

Handoff v1 accepted arbitrary nonempty strings for `readonly_paths` and
`writable_paths`, although the post-execution Git verifier already required
repository-relative paths. This allowed malformed or contradictory scope
declarations to reach dispatch. The change keeps the v1 wire shape and validates
both path lists during serialization and readback. Valid inputs keep the same
wire shape and values; the stricter rule rejects malformed, duplicate, or
conflicting data that v1 previously accepted.

The shared path rule is lexical: a value without a trailing slash names one exact
file; a trailing slash names descendants of that directory. Empty components,
absolute paths, NUL, backslashes, `.` and `..` are rejected. Duplicate entries
within either list and equal read/write grants are rejected. A readonly directory
may contain a narrower writable grant; an explicit writable directory may not
cover an explicitly readonly path. Prefix comparison follows path components.

This validates the declared handoff only. It does not restrict child filesystem
access, resolve aliases, or replace the host's permission system. The Git diff
checker remains a separate post-execution consistency check.

## Evidence-backed consumer map

| Producer / interface | Consumer | Contract | Evidence |
| --- | --- | --- | --- |
| `validate_repo_relative_path` in `scripts/engineering/developer_scope.py` | `validate_input` in `scripts/engineering/delegation_handoff.py` | Shared lexical grammar for incoming read/write paths | Test design `HANDOFF-PATH-01..08`; implementation verification pending exact PR head |
| `validate_repo_relative_path` | `verify_candidate_scope` in `developer_scope.py` | Writable grants and reported changed paths | `tests/test_developer_scope.py`, `DEV-SCOPE-01..14` |
| `validate_input` | Serialization and readback callers | Reject malformed handoff before it is accepted | `serialize_input` and `read_input` tests |
| Handoff v1 | Coordinator procedures and external consumers | Manual procedure is documented; external callers remain UNKNOWN | `docs/governance/CODEX-SUBAGENT-PILOT.md`; repository search |

No source consumer besides the tests and documented coordinator procedure was
found for the handoff serializer at the baseline. That does not prove there are
no external consumers; keep that edge UNKNOWN.

## Trust boundary and options

- Input comes from the task coordinator and may be stale or malformed.
- This module has no host ACL or agent-spawn authority; a validated path list is
  not a security boundary.
- Rejected: leave paths as arbitrary strings and depend on the later Git check;
  this permits invalid dispatch declarations.
- Rejected: reject all read/write containment; that would disallow a common
  readonly context directory plus one explicitly writable file.
- Selected: reuse the existing Git path grammar and allow only the narrower
  writable exception inside a readonly directory. Reject a broader write grant
  that covers a narrower readonly path.

The architecture method is `REUSE`d from
`docs/architecture/SOFTWARE-ARCHITECTURE-DECISIONS.md`; the existing handoff
contract is `EXTEND`ed. No new skill or approval mechanism is introduced.

## Migration and recovery

1. Recreate pending handoffs from trusted task scopes; do not normalize or trust
   a malformed scope supplied by a child.
2. Run the validator before dispatch and the existing Git scope check after a
   Developer handoff.
3. On rollback, revalidate pending handoff scopes or suspend their dispatch until
   checked. Preserve historical receipts as immutable records.
4. No filesystem or persisted-state migration occurs. Revert the validator,
   shared grammar export, tests, coordinator procedure, and this decision
   together if rollback is needed.

## Verification and handoff

| Case IDs | Expected behavior | Evidence |
| --- | --- | --- |
| HANDOFF-PATH-01..05 | Valid disjoint/narrower write scopes round-trip; malformed paths, duplicates, conflicts, and prefix confusion are handled as specified | `tests/test_delegation_handoff.py` |
| HANDOFF-PATH-06..08 | Exact-file/directory distinction, directional nesting, and write-directory sibling boundaries are tested through both entry points | `tests/test_delegation_handoff.py` |
| DEV-SCOPE-01..14 | Existing candidate-diff boundary and handoff regression suite remains green | `tests/test_developer_scope.py` |

Working-tree validation reports 51/51 focused handoff, scope, and role
configuration tests passing. The test-first regression was observed against the
baseline worktree. An independent Reviewer approved the implementation diff
before this ADR was added; review against a committed PR head is pending, as is
exact-head CI.
The negative review cases that reject a stale ADR SHA or unresolved migration
remain NOT_RUN. This helper is not packaged into Cloud Next, and the observed
Site source-pin smoke does not validate this change. Runtime for this candidate
is NOT_RUN; host-enforced ACL, role-profile loading, and token telemetry remain
UNKNOWN or NOT_RUN. The broader #767 worktree concurrency, shared-writer
serialization, and third-WIP control cases are outside this change and remain
unverified.
