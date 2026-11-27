# SDLC Deep runtime pilot — #748 / #768

**Scope:** validate one fresh bounded handoff-contract task in the Codex App Server runtime. This pilot is not a closure of #748 or #768.

## Candidate and code result

- GitHub `main` at start: `6c7a7070cc16dd70aa15f26f8553efaee76590c7`; its parent is `e4f96cc7c0e2b139c59f72d0b69bc880504b08a4`.
- C1 (`51433560c8dac8f7f398d301c4b4f1a8fef92214`) contains only the regression test. The independent Executor ran the exact new case; it exited 1 because `ValueError` was not raised for either read-only role.
- C2 (`485009558677e4273ac52dd85607d9a7e14d5821`) adds the validation rule. C3 (`6730fd3a8b4b110279e0a5225a337f0433159370`) adds a Developer compatibility case.
- C4 (`6690ff6475b317774c845bc496da18a2c5928ece`) refreshes the approved hashes in the existing source-continuation record and tests. A later documentation refresh describes the new acceptance rule; all frozen campaign hashes and release fields remain intact.
- The code rejects `PASS` with nonempty `changed_paths` for `sf-test-executor` and `sf-independent-reviewer`. It keeps empty-path `PASS`, `FAIL` paths, and Developer `PASS` paths valid.

## Role and test evidence

| Role | Host observation | Result |
|---|---|---|
| Test Designer | `gpt-6.1-terra`, medium | Froze `DH-RO-01..03`, `DH-DEV-01`, `DH-SHA-01`, and `DH-MAN-01`; designed the baseline RED and exact-SHA checks. |
| Developer | `gpt-6.1-terra`, high | Implemented C2, then addressed the Reviewer’s missing Developer compatibility case in C3. |
| Test Executor | `gpt-6-luna`, low | C1 RED; on C4, focused contract suite 10/10, handoff module 42/42, governance test 6/6. All C4 commands exited 0. |
| Independent Reviewer | Native collaboration child `/root/sf_independent_reviewer_c4`; requested Terra High, effective model/effort unavailable | Scoped review PASS; no actionable findings. Named profile activation and effective model remain UNKNOWN. |
| Architect | Requested `gpt-6.2-sol`, high in the pre-task runtime-boundary advisory; a separate C4 contract review returned A1 / EXTEND | No architecture or rollback blocker; effective child model/effort UNKNOWN. |

For App Server roles, `activePermissionProfile` was `null`: named TOML profile activation was not observed. The coordinator read each checked-in role definition and passed its instructions and requested model/effort. The `thread/start` response returned model/effort values matching the request, but `turn/started` and `turn/completed` omitted effective model/effort; therefore effective turn values remain UNKNOWN. Token usage was emitted for most App Server turns; the host exposed no financial cost.

## Post-rebase exact-SHA Test Executor run

On candidate `d839d18441ca741fb2c85f1349909338ee4ce867`, a fresh App Server Test Executor thread (`01a21ee0-dded-7423-8742-2691ba57fe27`) ran read-only. The `thread/start` response returned `gpt-6-luna` / `low`, matching the requested role settings; `turn/started` and `turn/completed` omitted model/effort, so effective turn model/effort remain UNKNOWN. `activePermissionProfile` was null. The turn completed, and token usage was observed (60,327 total tokens; 523 output tokens in final cumulative snapshot); financial cost was not exposed.

| Exact command | Exit | Summary |
|---|---:|---|
| `git rev-parse HEAD` | 0 | Matched candidate SHA |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.governance.test_sdlc_architecture_source_example -q` | 0 | 7 tests, OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delegation_handoff.FixturePolicyContractTests -q` | 0 | 10 tests, OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delegation_handoff -q` | 0 | 42 tests, OK |

The sanitized structured event data and output hashes are in [`runtime-e2e-01-receipt.json`](../../../runtime-canaries/sdlc-deep-2026-11-27/runtime-e2e-01-receipt.json) under `role_execution.executor_rebased_candidate_d839`; no conversational response is retained. This establishes the bounded Test Executor task only, not end-to-end release acceptance.

## PR-head exact-SHA Test Executor rerun

Before this dispatch, the `sf-test-executor` INVOKE decision was recorded in [`executor-post-ci-rerun-invoke.json`](../host-runtime-capability/executor-post-ci-rerun-invoke.json). A fresh App Server thread (`01a21eed-0b1d-7073-95fa-b303b21d3b8a`) ran read-only at exact PR head `6ab966064eb98f34b62fc23a52b742aafaefd138`; all commands exited 0: governance 7/7, focused fixture-policy 10/10, and handoff module 42/42. `thread/start` returned `gpt-6-luna` / `low`; the turn lifecycle omitted effective model/effort, so both remain UNKNOWN. Named profile activation remains UNKNOWN (`activePermissionProfile=null`). Token usage was observed; currency cost was not exposed. Structured event data and output hashes are stored in [`runtime-e2e-01-receipt.json`](../../../runtime-canaries/sdlc-deep-2026-11-27/runtime-e2e-01-receipt.json).

## Runtime permission check

The first `workspaceWrite` probe used only a `tests/` writable root. Its effective thread roots also included `/private/tmp` and the host temp directory, so both the allowed and out-of-grant writes succeeded. Both synthetic markers were inspected and removed. This was an ACL failure.

The corrected turn requested `excludeSlashTmp=true`, `excludeTmpdirEnvVar=true`, `runtimeWorkspaceRoots=tests/`, and a `tests/` write root. In the Developer role turn, the allowed test marker was created; the repository-root marker outside that grant failed with `PermissionError errno=1` and remained absent. The allowed marker was inspected and removed. **Filesystem ACL: PASS for this one bounded App Server turn.** The effective turn policy itself was not returned as host metadata; the actual command outcome is the denial evidence. This does not establish MCP, secret-read, deployment, or universal per-role ACLs.

## App Server thread-start schema observation

The schema was regenerated on 2026-11-27 with Codex CLI 0.159.1 using
`codex app-server generate-json-schema --experimental`. The generated
`v2/ThreadStartParams.json` SHA-256 was
`80a40a7fac15b4bf70efb7f893fb353acc0a0d30c68f54aee4f01923deca85de`.
It exposes top-level `sandbox`, `permissions`, `runtimeWorkspaceRoots`, and
`dynamicTools`; the latter declares function or namespace function tools. It
does not expose top-level `mcpServers` or `parentThreadId`. However, `config`
allows additional properties, so this schema does not settle whether a config
override can scope MCP servers. **MCP-tool ACL remains NOT_PROVEN** until a
negative invocation is denied by the runtime or the host contract establishes
an enforced per-role selector. This finding is specific to this App Server
version and surface.

## Interruption and fresh-thread handoff

Stage A’s Terra High Developer turn was interrupted while a bounded wait command was active. A distinct Luna Low Test Executor thread then received a 911-byte serialized handoff (SHA-256 `8caea92dee8fbf3e6c131236f376930ad0601b4ea39ac172652767c7e3e7b719`), reserialized it byte-identically, and rejected C1’s receipt against expected C4 with `candidate SHA mismatch`. An input containing `approval` was rejected by the serializer before dispatch.

**Resume handoff: PASS** for that limited case. No approval had been issued in Stage A, so approval non-transfer remains `NOT_RUN`. MCP ACL and native Desktop child lineage remain `NOT_RUN`.

## Architecture and release state

The source-level change is A1 / EXTEND at `validate_result`; it preserves v1 fields and signatures, but tightens acceptance of read-only role `PASS` results. If reverted, revert the rule, tests, documentation, and continuation pins together; suspend acceptance of affected pending `PASS` receipts until revalidated. Historical receipts remain unchanged.

The continuation remains `INTEGRATION_ISOLATED`, runtime `NOT_RUN`, and release approval `false`. No Site deployment occurred. Keep #748 and #768 open until native-child routing, MCP/tool ACL, approval non-transfer, complete role/profile evidence, and the remaining campaign gates are separately verified.

Machine-readable sanitized runtime receipt: [`runtime-e2e-01-receipt.json`](../../../runtime-canaries/sdlc-deep-2026-11-27/runtime-e2e-01-receipt.json). Test plan: [`test-plan.md`](test-plan.md).

## Per-thread MCP tool ACL canary (2026-11-27)

The independent A2 architecture recommendation and frozen Test Designer plan led
to a local no-model App Server canary on candidate
`68a950216aaffff150bdde640a955aa3b8c79ac5` using `codex-cli 0.159.1`. The
replayable harness first passed 9 focused unit tests; the exact candidate was
then independently checked by the read-only Test Executor and reviewed by the
Independent Reviewer. Both roles accepted this exact SHA before runtime.

The three validated commits were replayed on a clean branch from current main.
The Independent Reviewer approved the byte-identical code tree, and the
read-only Test Executor passed all 9 tests on exact PR HEAD
`ac40b4204fcd34a7d168febb047de6b113588250`. The canary was rerun against that
exact PR HEAD; the linked receipt binds to it.

The canary ran two isolated App Server processes, one for `enabled_tools` and
one for `disabled_tools`, each with baseline and per-thread restricted MCP
configuration and a local two-tool stdio fixture. No model turn, hosted MCP,
Site deployment, or production integration was used. In both runs, the
restricted thread's catalog contained only `allowed`, the baseline catalog
still contained both tools, an allowed call reached the fixture, and a direct
`forbidden` call returned the host denial
`tool 'forbidden' is disabled for MCP server 'canary'`. The fixture log had
zero forbidden-call ingress and exactly one baseline, allow, and barrier call.
Both App Server processes exited 0; all fixture processes observed shutdown and
were absent; no residual process group or temp path remained.

**Disposition: PASS, narrowly scoped to Codex App Server 0.159.1 direct
JSON-RPC per-thread MCP filtering for both documented configuration keys.**
The receipt is
[`appserver-mcp-tool-acl-canary.json`](../../../runtime-canaries/sdlc-deep-2026-11-27/appserver-mcp-tool-acl-canary.json).
This supersedes the earlier `NOT_PROVEN` schema-only statement for this exact
surface/version. It does not establish Desktop native-child inheritance,
Cloud Next/hosted integration enforcement, role-to-profile activation, model
selection, or a full Developer→Executor→Reviewer→rework cycle. The harness
blocks PASS if candidate source/index/worktree changes or cleanup remains.
