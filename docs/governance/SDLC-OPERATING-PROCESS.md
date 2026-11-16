# Skills Factory delivery process — adopted 2026-11-16

This is the owner-approved D1–D8 operating process. It supersedes the global
single-active-iteration restriction, not frozen historical acceptance criteria.
Reuse existing Issues, Project fields, receipt schema, evals and deployment tooling.

## Ownership and flow

The owner chooses outcomes and material risk. The coordinator selects ready work,
resolves dependencies and integrates it. The implementer supplies code and tests;
the reviewer assesses behavior and evidence. A self-review must be called one.
Security, destructive data changes and release-gate changes need another reviewer;
absent that review they remain unapproved. Production authorization is separate.

Use native **Backlog → Discovery → Ready → In progress → In review → Verification → Done**.
Blocked is a label plus cause, owner and resumption condition, not another stage.
Merge moves runtime-bearing work to Verification. Done requires that task's actual
acceptance evidence; cancelled/not_planned is not successful implementation.
Production promotion is not implied by Done.

Each Issue states one result, boundaries, numbered acceptance criteria, dependency
and architecture impact, verification and evidence links. Use the existing Task
Definition Contract; do not introduce another handoff or duplicate Project fields.
Clarify a material ambiguity before implementation, not at closeout.

## D2: bounded parallel work

Maximum active development WIP is **2**, with one shared Lab candidate at a time.
Project stages In progress and In review consume a development slot; an explicitly
blocked/parked package does not. Verification does not hold a development slot.
Two packages may not concurrently change the same shared interface/migration
without an integration order and owner. Use separate branches/worktrees.
Iteration is a planning grouping, not a repository lock. Dependencies, not sequence
numbers, control the start of independent work. Keep scope and historical outcomes.

`scripts/governance/delivery_control.py` audits native Project WIP with pagination.
The existing serialized metadata workflow checks WIP before moving work into an
active stage and reads back mutations. Direct manual Project edits still require
the coordinator's check; this is not a GitHub-native transaction/branch-rule lock.
Lab lane ownership is coordinated explicitly; no new deployment credential is added.

## D4/D7: architecture and test selection

Use native **Architecture Impact A0–A4**, with substantive rationale in the Issue.
Do not create K0–K3 or a competing architecture classification.

| Impact | Minimum consequence |
| --- | --- |
| A0 | Result/document validation; no runtime change implied |
| A1 | Component tests and preserved-interface regression |
| A2 | Extension boundary, reuse/capability check, consumer regression |
| A3/A4 | Architecture approval, contract/consumer map, migration/rollback and cross-component regression |
| UNKNOWN or incomplete consumer map | Broader affected-channel baseline; discovery where design cannot safely proceed |

Security/data risk can require additional review regardless of A-level. Test scope
is the union of architecture impact, changed behavior, direct/transitive consumers,
routing neighbors, risk and actual host/channel. Three unassisted critical routing
attempts are an initial smoke policy, not a reliability estimate. Independent arithmetic
or a substantive rubric supplies the oracle. Include sufficient-data cases as well
as missing-data/stop cases. Do not change expected results merely to pass.

`scripts/engineering/change_gate.py` consumes the explicit A-level, changed paths,
reviewed consumer paths and security flag. Its output is a plan, never runtime PASS.
The Project field remains canonical; CLI inputs are projections, not proof of a
Project update. Unknown impact expands rather than silently shrinking regression.
During this pilot existing offline CI suites remain required; runtime selection is
impact-scoped. Broader offline skipping needs a separately validated dependency map.
CI records actual Git-diff paths and conservatively uses UNKNOWN until a reviewed
native Project assessment is supplied through a trusted channel; it does not guess
an A-level from filenames or silently skip tests based on untrusted PR prose.

## D1/D6: integration and release gates

Integration validates readiness **structure and integrity**, not calendar production
eligibility: `validate_readiness.py --target integration`. Broken records, missing
receipts claimed verified, policy weakening and known high-severity failures fail.
Pending runtime is visible, not PASS. No dates are renewed to green a PR.

Production uses `--target production` (the safe CLI default), retaining expiry checks
and rejecting pending runtime evidence, including unexpired exceptions. It also
requires existing promotion/provenance checks and owner authorization. A Lab candidate
may be deployed to obtain runtime evidence, clearly marked unaccepted until observed.

Ordinary test evidence has an automatically captured run time and immutable source,
fixture and environment identity. Its compatibility changes when relevant dependencies
or environment change. Review dates are reminders; an accepted exception's expiry
applies only to its defined use. Do not require four new dates per record. Existing
registry fields are preserved, not mass migrated or backdated.

## D3: evidence and artifacts

GitHub is the center: Issues/Projects for work, repository for definitions and safe
small receipts under existing evals/results, Actions artifacts for larger outputs.
No Drive status sheet, new database or second manual evidence ledger.
`scripts/eval/evidence_index.py` produces a deterministic, allowlisted projection of
existing receipts outside product sources. It preserves FAIL and invalid historical
records; matching component identity alone never proves environment compatibility.
It omits prompts, responses, traces and narrative notes. Publication of sensitive
raw evidence requires a separately approved private destination.

`sf-evidence-<source SHA>` contains the generated index and a candidate-bound manifest.
Use `artifact_bundle.py verify --directory <download> --candidate <expected SHA>`;
include `--fixture-sha256` when QA is fixture-specific. Wrong candidate, different
fixture, changed files, added files and symlinks fail. This verifies identity/integrity,
not behavior or cryptographic issuer authenticity. Use the existing authenticated
artifact download tooling; do not bypass access restrictions or shuttle successive
ZIPs through the owner by default. Retain accepted artifacts before Actions expiry;
90-day retention is not permanent archival. Copy public-safe release assets via the
existing release procedure; do not automatically publish private logs.

Historical support pins for Iterations 07/08 are verified at the immutable commit
recording their manifest by `scripts/eval/historical_support.py`: readiness metadata,
generated catalogs and the old evaluator. This can postdate runtime execution;
it is administrative provenance, not new runtime acceptance. Manifests/receipts are
not rewritten by the validator.
Behavior sources, fixtures, rubrics and receipts still require live matching identity.
Archived administrative integrity does not approve current runtime or current release.
Unavailable anchor or wrong pin fails closed; CI must fetch full history.

## D5: autonomy, blocking and deployment

The owner authorized in-scope implementation, tests, PR, merge after required checks
and the existing private Lab. This is not permission for production, new spend,
destructive actions, disclosing private data or expanding access. Tool policy and
explicit automatic-review rejection remain binding. Use the existing publishing
runbook and managed credential path; do not transport tokens to evade a denial.

One blocker record holds cause, evidence, impact, owner and concrete resumption
condition. Retry a transient fault or test a new hypothesis; do not rerun a complete
audit when nothing changed. Resume on an event or work on an independent ready task.
Report result, evidence, remaining gap and next step. Ask the owner for a material
decision, not routine interpretation of an unambiguous test.

Prepare one reproducible environment with
`python3 scripts/engineering/bootstrap.py`; `--check` checks without installation.
Use the resulting .venv interpreter and resolved .tmp/python-tests TMPDIR. Keep the
same hash-locked dependencies as CI. A broken checkout is preserved and replaced by
a clean one; do not reset unknown edits. A harness/environment error is not silently
classified as a product defect.

Deploy the tested artifact, or prove content equivalence if the host rebuilds it.
Keep canonical commit, mirror commit and observed deployment identity distinct.
After deployment check identity and critical behavior. Record failures without raw
private prompt telemetry by default. Roll back to a known good artifact within the
authorized scope; irreversible migrations need recovery/forward-fix planning.

## D8: pilot and measurable acceptance

Pilot the process on five genuinely completed subsequent changes covering metadata,
deterministic logic and behavior/runtime. This adoption change is not five successful
pilots and does not validate all product skills. Use existing Issue/PR/run timestamps
to compare lead time, blocking causes, manual artifact transport, synchronization-only
PRs, CI/model cost where available, and escaped material defects. No invented baseline.

Required process regressions: unrelated expiry does not stop integration; production
still rejects expiry/pending/failure; changed runtime/fixture cannot inherit old PASS;
administrative updates do not rewrite historical manifests; WIP 2 permits independent
work and blocks a third active package; public index omits raw content; artifact identity
checks reject the wrong candidate. Revisit WIP/selection after the pilot if collisions
or missed dependencies appear. Keep review and acceptance explicit.
