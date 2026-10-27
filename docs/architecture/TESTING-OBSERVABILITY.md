# Testing and runtime observability

This design extends the existing evaluation protocol; `evals/`, campaign locks,
receipts and isolation rules remain canonical. Promptfoo is an optional pinned
adapter for deterministic MCP contract/routing regressions. It does not own
cases, rubrics, or verdicts, and it does not replace the repository runner.

## Test layers

| Layer | Runs | Trigger | Cost boundary |
| --- | --- | --- | --- |
| Deterministic contracts | static validators, unit tests, schema and package checks | every pull request | no model calls, local fixtures only |
| Smoke regression | selected repository cases through local/test MCP | pull request when runtime code changes; manual locally | bounded, synthetic only |
| Full regression | canonical campaign against a version-pinned candidate runtime | main or manual dispatch | explicit approval/runner, no production writes |
| Failure-state simulations | timeout, permission, missing-tool, schema and renderer fixtures | manual workflow dispatch | offline; no provider calls or runtime PASS |

The campaign receipt remains the source of truth. Harness output is imported
into that receipt with the exact source/runtime identity; a green Promptfoo
process alone is not a runtime PASS.
The manual failure workflow validates only that simulated failures stay
offline and are labeled `NOT_RUN`; executed model-level red-team verdicts still
need the existing isolated campaign and independent review.
The Promptfoo provider exposes only the local identity, catalog, skill-load
and investment-router tools; it has no production write capability. Persistence
cases should start with resettable fixtures or an ephemeral local/Postgres
store. A durable Supabase TEST target is justified only by a documented need
for cross-session persistence or remote-store realism.

## Trace contract

The MCP runtime emits one OpenTelemetry span per tool invocation. Each span
uses the trace ID as `run_id` and records the deployment environment, source
revision, tool/capability identity, version/digest when available, duration,
status, error type, and whether external reads or writes occurred. Current MCP
tools perform no external reads or writes, so both are explicitly `false`.
Arguments are hashed before export. Prompts, raw arguments, results, skill
instructions, secrets, exception messages and model reasoning are excluded.
Receipts carry the same `run_id`, making a single tool invocation auditable;
the MCP host must supply a conversation/run correlation ID before separate
tool calls can be represented as one multi-step trace.

Export is disabled unless an OTLP endpoint is configured. A local Phoenix OSS
instance can receive OTLP/HTTP traces at `http://127.0.0.1:6006/v1/traces`.
For example, run a pinned local release with:

```sh
PHOENIX_TELEMETRY_ENABLED=false PHOENIX_ALLOW_EXTERNAL_RESOURCES=false \
PHOENIX_WORKING_DIR=.tmp/phoenix \
uvx --from arize-phoenix==20.26.1 phoenix serve
```

The runtime can then be launched with
`OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1:6006/v1/traces`.
Phoenix is a local debugging surface; traces stay on the developer machine.

## Promptfoo Community adapter

`scripts/eval/promptfoo/` pins Promptfoo and starts the repository MCP server
over stdio. Its smoke cases are deliberately a small view of the canonical
routing registry, not a copy of the eval corpus. Behavioral model evaluation
continues through the isolated executor packs and receipts under `evals/`.
Set `SKILLS_FACTORY_MCP_ROOT` to a built package root to run the same smoke
against that exact local artifact; otherwise it uses the source MCP adapter.
No account, plugin, paid SaaS, or external inference is needed for the
deterministic MCP contract smoke. The target cost is 0 PLN in platform fees
at this stage, excluding inference and CI use that exceeds free limits.

## Responsibilities and overlap

| Existing work | Owns | ENG-22 adds |
| --- | --- | --- |
| ENG-08 / ENG-09 | local preflight and test design contracts | target architecture only |
| ENG-11 / ENG-12 / ENG-20 | lifecycle, capabilities, release evidence | shared trace fields and trigger tiers |
| E2E-01..05 | browser/runtime behavior, failure paths and parity | no replacement of their runners or evidence |
| #240 local runner | isolated local model execution | optional deterministic MCP regression adapter |
| #248/#250 runtime identity/receipts | runtime identity and bounded receipts | trace/run correlation and export |

The current GitHub Actions workflow already separates source/security,
governance, domain, eval integrity, artifact builds, and runtime handoffs.
This architecture keeps those checks and labels their cost/coverage rather than
introducing a parallel full-campaign job on every pull request.
