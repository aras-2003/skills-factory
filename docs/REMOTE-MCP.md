# Remote MCP deployment contract

`runtime/mcp/server.py` is the single MCP entrypoint for local and remote
profiles. The compatibility path `runtime/mcp/cloud_server.py` delegates to it.
It exposes these headless tools:

- `runtime_info`
- `list_skills`
- `load_skill`
- `route_investment_request`
- `render_bar_chart`
- `render_line_chart`

`runtime_info` is read-only and reports deployment identity. Missing identity
is returned as `attestation_status: unattested`, never as a compatible release.
Exact-version receipts should include `release_id`, `source_revision`,
`channel`, `capability_contract_version`, `tool_schema_digest` and `deployed_at`
before a Lab/Site parity or release decision is marked PASS.

The bundled Lab catalog is the source of workflow instructions for both the
Lab and the MCP profile. `list_skills` exposes the packaged catalog and
`load_skill` returns the exact packaged `SKILL.md` plus its content digest for
host-model execution. The MCP server does not independently perform model
reasoning; it loads the same instructions that the Lab packages, while the
host model executes them. Routing does not execute the selected workflow. For
investment requests, the server returns
`execution_state: routed_only` and `workflow_executed: false`. The host must
load the exact selected child with `load_skill` and then follow its instructions.
The routing fields describe the router tool call; they do not mean the host must
stop after successfully loading the child. If the child or a required provider
is unavailable, the host must report BLOCKED/NOT RUN and must not invent an
execution receipt. These instructions are model-facing guidance rather than a
technical enforcement boundary, so each supported host still needs a runtime
evaluation that proves routing, child loading, and stop behavior for missing
providers in a fresh chat. Unrelated tasks must not be routed merely because
they contain a negated or quoted investment term.

Lab executor inputs are stored outside the `skills/` tree in `executor-inputs/`
and indexed by `executor-inputs.json`; they are not returned by `load_skill`.
Evaluator rubrics remain repository-side. Legacy Lab-only eval appendices are
stripped by the loader. Each MCP tool response includes an unsigned
`tool_receipt` with canonical input/output SHA-256 digests and source revision.
Receipts record tool execution only; they are not signatures or deployment
attestations. Chart receipts report `artifact_state: rendered` and
`client_display_state: not_observable`. Renderer failures include a failure
receipt with the error type and digest, without exposing raw error text.

## Required deployment properties

The chosen host must:

1. expose the ASGI `app` from `runtime/mcp/server.py`;
2. serve streamable HTTP MCP at a stable HTTPS `/mcp` endpoint;
3. enforce authentication at the edge when the endpoint is not strictly
   private to the owner;
4. keep secrets and user credentials outside the repository and runtime
   source tree;
5. provide health checks, request logs without sensitive prompt contents, and a
   rollback path for incompatible tool schemas.

The repository intentionally does not choose a cloud vendor or commit a
deployment credential. A concrete host and endpoint are release inputs, not
source defaults.

## Package after deployment

```bash
python scripts/package/build_plugin.py \
  --runtime-mode remote \
  --remote-mcp-url https://<your-host>/mcp \
  --output .tmp/chat-web
python scripts/package/artifact_validation.py .tmp/chat-web
```

The resulting profile contains the production skills and an HTTPS MCP mapping,
but no bundled local MCP executable. For mobile Chat, build and distribute the
`skills-only` profile instead:

```bash
python scripts/package/build_plugin.py \
  --runtime-mode skills-only --output .tmp/chat-mobile
python scripts/package/artifact_validation.py .tmp/chat-mobile
```

Do not mark the remote profile as mobile-compatible merely because the package
build succeeds. Mobile MCP support is a host capability and must be validated
separately from repository/package validation.
