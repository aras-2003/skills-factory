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

## Role and model routing

For A2, explicitly dispatch the Codex role profile
`.codex/agents/sf-architect.toml` (`gpt-6.2-sol`, high) when a capability
boundary, shared contract, or material dependency changes. A3/A4 decisions
require this architecture advice. Also dispatch for an A1 change that affects
a shared public contract or trust boundary. The profile is advisory; the
coordinator retains scope and integration ownership. Do not routinely dispatch
it for cosmetic A0 work or an A2 change without those material triggers.

The OAF `architecture-review` skill and its parent workflow address enterprise
or organisational architecture. Their `standard`/`strong` model-class guidance
is not a Codex agent selection rule and does not override the software
`sf-architect` role profile. Invoke OAF capabilities only when the request is
actually about enterprise/organisational architecture. If the host cannot
spawn the named role or expose its effective model, record that gate as
`BLOCKED`/`UNKNOWN`; TOML values and a different model's answer are not runtime
proof.

## Input and output contract

Input must include the GitHub Issue and numbered acceptance criteria, exact baseline SHA,
candidate SHA when available, changed paths, reviewed direct and transitive consumers,
with their source paths, public schemas/interfaces, trust boundaries,
Architecture Impact field as actually recorded, relevant tests, constraints,
and required approval owners. Missing items are explicitly `UNKNOWN`.

The `change_gate.py` CLI resolves the selected base/source revisions and checks
that each named consumer exists in the selected source tree. A present file is
not proof that the relationship is complete. `--graph-reviewed` records a
caller claim only; absent a machine-verified complete graph, material changes
retain the full affected-channel baseline. The pure `plan()` helper remains a
static planner and cannot prove Git provenance by itself.

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

## Shared typed-contract example

`docs/architecture/decisions/2026-11-load-skill-source-pin.md` is the
source-pinned analysis of the Python MCP and Cloud Next `load_skill` consumers.
The owner accepted an optional expected-source input with the same logical
mismatch code/message across backends while allowing backend-specific receipt
metadata. PR #777 implemented the contract and parity tests; it is present on
canonical main `9b6fce4a5e08dc527309cccb5411ebb086269569`. The deployed Lab
accepted an omitted or matching pin and rejected a stale pin without returning
instructions. Python MCP contract tests cover malformed pins, unknown fields,
and unverifiable packaged metadata.

This decision binds returned instructions to a requested source revision. It
does not establish per-role tool ACLs or host permission enforcement; those
remain unavailable on the observed spawn surface.

### Migration and rollback for this example

The optional parameter adds no persisted runtime state, but rollback is conditional.
Before any caller adopts the parameter, both backends may remove it together. After
adoption, prove callers have stopped sending it before reverting both schemas. While
consumer adoption remains unknown, retain support and fix forward; never silently
ignore a supplied pin. Regenerate the catalog/attestation and rerun both backend
contract suites for a rollback. Do not add guessed `allowed_tools` or `path_scope` keys as an alternative:
those remain unsupported on the observed spawn surface.

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
