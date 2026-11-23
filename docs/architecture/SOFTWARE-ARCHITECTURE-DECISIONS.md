# Software architecture decisions for repository changes

This method supports issue #766 for source and tooling changes with material
cross-component impact. It is not the OAF enterprise `architecture-review` skill,
the UI `implementation-brief`, `skill-specification`, or the deterministic
test-selection behavior of `scripts/engineering/change_gate.py`. It does not
approve a merge or release.

## When to invoke

- A0/A1: do not routinely invoke the Architect; use a short implementation
  plan and preserved-interface regression when the impact and consumers are
  known.
- A2: ask for advice when a capability boundary, shared contract, or material
  dependency changes.
- A3/A4: require architecture advice for cross-component contract, trust,
  deployment, migration, or data-impact decisions, then obtain the independent
  review required by the operating process.
- UNKNOWN impact or incomplete consumer evidence: broaden discovery and tests;
  do not assume the graph is complete.

## Input and output contract

Input must include the GitHub Issue and numbered acceptance criteria, exact baseline SHA,
candidate SHA when available, changed paths, reviewed direct and transitive consumers,
with their source paths, public schemas/interfaces, trust boundaries,
Architecture Impact field as actually recorded, relevant tests, constraints,
and required approval owners. Missing items are explicitly `UNKNOWN`.

The decision record contains:

1. Issue, baseline/candidate SHA, impact and decision status.
2. Source-backed current and proposed component boundaries. Add a sequence or
   deployment view only when it resolves a material ambiguity.
3. Producer/consumer paths and public typed contracts, including compatibility
   and version behavior. Mark unverified edges `UNKNOWN`.
4. `REUSE`, `EXTEND`, `COMPOSE` or `CREATE`, with overlap evidence and the
   alternatives rejected.
5. Trust boundaries, security properties, environment/deployment constraints,
   and failure behavior.
6. Migration steps, rollback or forward-fix path, data compatibility and
   operational risks.
7. Acceptance cases and tests, unresolved questions, explicit approval
   requirements, and bounded handoff paths for implementation and test.

Before accepting the decision, compare its source SHA and consumer set with the
actual diff. A changed shared contract invalidates prior approval until
the affected decision and consumers are reviewed again. The code owners and
existing architecture/test gates retain approval authority.

## Repository example: extending the role profile contract

On baseline `6fd06a08b82c8903713a7242fddf8cd12bc69dba`, the role contract is
consumed by `.codex/agents/*.toml`, `.codex/config.toml`, `AGENTS.md`,
`docs/governance/CODEX-SUBAGENT-PILOT.md`, and
`tests/test_codex_agent_team.py`. This SDLC Deep change adds a separate matrix
that makes enforcement states explicit while preserving agent names, TOML
semantics, the two-thread limit, handoff fields and existing routing. That is a
safe **EXTEND** of the documentation/test contract. A proposed TOML
`allowed_tools`/`path_scope` key would be a breaking and unsafe substitute:
the observed spawn API has no such per-child control, so it could be ignored or
misrepresented as enforcement. Reject that option unless supported host
documentation and an actual permission-negative test prove its behavior.

This example is source grounded, but its runtime controls remain unavailable
on the observed host surface; the decision cannot be interpreted as proof of
least-privilege enforcement.

### Migration and rollback for this example

The selected extension adds project-local guidance and an explicit capability
matrix while retaining the existing TOML keys, agent names, and two-thread
limit. It has no runtime state migration. Before adopting it, validate the
existing profile/config files and run the agent-team, handoff, and governance
contract tests against the candidate SHA. If review finds a contract mismatch,
revert the matrix, the two Developer instruction edits, and this workflow
addition as one candidate change; then rerun those checks. No user data or host
configuration needs restoration. Do not add a guessed `allowed_tools` or
`path_scope` key as a rollback substitute: those keys remain unsupported on the
observed spawn surface.

## Stable architecture test cases

| Case | Input | Expected result | Forbidden result |
| --- | --- | --- | --- |
| `ARCH-01` | A1 local change with known consumers | Skip routine Architect call; preserve current interface. | Escalating every edit to A2. |
| `ARCH-02` | A3 typed schema used by two source-confirmed consumers | Show both producers/consumers, compatible extension, breaking alternative and migration/rollback. | Claiming compatibility from schema name alone. |
| `ARCH-03` | Incomplete dependency graph | Mark missing edges `UNKNOWN` and broaden consumer checks. | Treating absent graph edges as proof of no consumer. |
| `ARCH-04` | Data or deployment migration | Give ordered migration and rollback/forward-fix with compatibility constraints. | Rollback that cannot restore changed data. |
| `ARCH-05` | ADR SHA differs from current baseline or material diff | Invalidate the stale decision and re-review. | Reusing approval because the file title is unchanged. |
| `ARCH-06` | Request routes toward enterprise architecture, UI brief or skill specification | State the boundary and route to the existing capability when applicable. | Creating a duplicate software architecture skill without a distinct-method review. |
| `ARCH-07` | High-risk trust-boundary or permission decision | Surface security constraints, owner approval and a negative test. | Treating prompt instructions as access control. |

An independent reviewer assesses the decision against the real diff, cases,
consumers and migration. Missing exact SHA, an unresolved material consumer or
an unsafe migration blocks the gate. This review is separate from the
Architect's advice and from CI status.
