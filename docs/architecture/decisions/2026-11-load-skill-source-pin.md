# `load_skill` source-pin decision

- Issue: [#766 — Software architecture decision and contract-review capability for A2–A4](https://github.com/aras-2003/skills-factory/issues/766)
- Criteria: AC-02, AC-03, AC-05, ARCH-02, ARCH-03, ARCH-05, ARCH-07
- Architecture Impact: A2 proposed for the shared tool contract; native project field not independently verified.
- Decision: owner approved the optional source pin and the invalid and mismatch errors. The fail-closed unverifiable error is an engineering assumption, not an additional owner-approved case.
- Historical implementation baseline SHA: `1bc7677b6c63427a20b3e9f2595dce797905542b`.
- Historical implementation candidate SHA: `5cedbb5354913b9299818c048400b72a976fff17`.
- Current consumer-map source SHA: `242fe4762d2b2c6cc2c602720d222e1276c0cd17`.
- Historical validation follow-up: [PR #786](https://github.com/aras-2003/skills-factory/pull/786), based on canonical `main` `f10c7d17674a1e5095fcaead7b03cbec10707ad2` and merged as `337b2b6b44db18f0261d16441e4587f90febc40c`.
- PR #786's review, CI, and deployed-channel checks apply to that historical candidate; they do not certify the later consumer map or later source changes.

## Context and decision

`runtime/contracts/mcp-tools-v1.json` keeps `skill_name` as the only required
input. Python MCP and Cloud Next expose the same optional
`expected_source_revision`: a lowercase 40-character hexadecimal Git commit
ID. An omitted value preserves existing calls. A supplied value is a
comparison only and cannot select a Git ref, path, URL, or package. Unknown
fields are rejected. Both adapters return these stable errors before returning
instructions:

- `INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID.`
- `SOURCE_REVISION_MISMATCH: The packaged skill source does not match the requested revision.`

If package identity cannot be checked, a supplied pin fails closed with
`SOURCE_REVISION_UNVERIFIABLE: Packaged source revision could not be verified.`
The backends may wrap errors or add receipt metadata differently; the code and
message are the logical contract. Errors do not disclose input or actual
revision, paths, or instructions.

Python compares against the adjacent package manifest and verifies that the
packaged `skills/` payload matches its digest before a matching pinned load.
After pin syntax validation, Python verifies identity and payload integrity
before comparing revisions. A valid stale pin with a damaged payload therefore
returns `SOURCE_REVISION_UNVERIFIABLE`; with an intact payload it returns
`SOURCE_REVISION_MISMATCH`. This scans the packaged payload even for stale pins.
This unsigned manifest and digest demonstrate payload consistency, **not
origin authentication or deployment attestation**. Cloud Next uses the
embedded Lab release revision, generated from a digest-checked Lab package;
it checks embedded identity metadata at runtime, not the package bytes again.
The Site deployment mirror revision is a separate identity. Neither check
establishes execution by a host model.

### Server-owned classification of malformed calls

The optional `expected_source_revision` property is advertised without a JSON
Schema `type`, length, or pattern constraint. The server owns validation so
malformed strings, JSON `null`, and numbers can reach both backends and receive
the approved `INVALID_SOURCE_REVISION` code/message instead of connector-level
schema diagnostics. `skill_name` remains required and string-typed, but its
length is not constrained at discovery. Unknown properties remain rejected
before either value is inspected. This is an interoperability trade-off:
clients must send the supplied pin unchanged, and connector compatibility
with the deliberately permissive discovery schema must be verified on each
deployed channel before callers rely on it.

For PR #786, a supplied revision is checked for format and packaged identity
before semantic validation of an empty, string-typed `skill_name`. Thus a
malformed or stale pin keeps its stable source-revision error when both string
values are invalid. Missing or non-string names are outside the shared error
precedence guarantee because backend schema boundaries can classify them
differently. Unknown properties still fail first.
Only the logical code/message is shared across adapters; MCP envelopes and
receipts retain backend-specific metadata.

Requiring the field was considered and rejected: existing clients send only
`skill_name`, and making it mandatory would require a coordinated versioned
migration without evidence of a need for that break.

## Reuse decision

`REUSE` the existing repository method in
`docs/architecture/SOFTWARE-ARCHITECTURE-DECISIONS.md` and
`templates/architecture/software-decision.md`. This worked example strengthens
that method with a source-confirmed consumer map; it does not introduce a
separate software-architecture skill or duplicate approval workflow. Reconsider
a reusable skill only if repeated cross-repository use demonstrates a distinct
method from the existing enterprise architecture and skill-specification
capabilities.

## Current source consumer map

This map binds the 34 listed source files to reviewed commit
`242fe4762d2b2c6cc2c602720d222e1276c0cd17`. The governance regression verifies
that listed files are byte-identical at that commit except for the exact
successor deltas recorded below. The continuation manifest permits only
refreshed digests for the approved source deltas, this ADR, and its governance
test; each digest is checked against its current file. It separates runtime tool consumers from
ingress, evidence and release verifiers, and build-time producers; finding a path does not imply
that it sends the optional `expected_source_revision` pin. This is a
source-confirmed inventory of the listed paths, not proof that the repository
consumer graph is complete.

### Runtime and transport consumers

- `runtime/contracts/mcp-tools-v1.json` is the shared versioned tool schema,
  a contract input for backend conformance, not a runtime caller.
- Python MCP registers `load_skill` in `runtime/mcp/server.py` and reads the
  packaged catalog through `runtime/mcp/skill_catalog.py`. The compatibility
  HTTP entry point `runtime/mcp/cloud_server.py` imports the same server and
  starts Streamable HTTP; it is not a second implementation. The supported
  ASGI deployment exposes the same `server.app` as documented in
  `docs/REMOTE-MCP.md`, not a separately versioned handler.
- Cloud Next receives MCP requests in
  `adapters/skills-factory-cloud-next/src/mcp-handler.ts`, validates and
  dispatches them through `adapters/skills-factory-cloud-next/src/cloud-tools.ts`,
  and loads the generated embedded catalog. The Site `/mcp` route in
  `sites/skills-factory-site/app/mcp/route.ts` exports POST/GET/DELETE to
  that handler, but `mcp-handler.ts` accepts only POST and returns 405 for
  GET/DELETE. `scripts/package/build_cloud_next_site.py` binds the generated
  bundle's mirror identity to the canonical Skills Factory source revision.
- The Site browser surface in `sites/skills-factory-site/app/page.tsx` imports
  `callTool`; its WebMCP `document.modelContext.registerTool` callback and the
  interactive console both call that adapter. Its sample `load_skill` request
  sends `skill_name` only. The shared `TOOLS` schema is registered with
  WebMCP, so pin availability depends on the generated bundle; the sample
  itself does not demonstrate pin adoption.

### Site ingress and provenance

- `sites/skills-factory-site/build/sites-worker.ts` is the deployed worker
  ingress for `/mcp` and delegates to the Site adapter handler. The build
  configuration in `sites/skills-factory-site/vite.config.ts` selects this
  worker entry point; neither file defines another `load_skill` contract.
- `sites/skills-factory-site/scripts/sync-site-source.mjs` synchronizes the
  canonical source into the provider-managed Site workspace. It is a
  publication/provenance step, not a runtime caller.
- `adapters/skills-factory-cloud-next/src/tool-receipt.ts` formats tool
  receipts and source identity metadata; it observes tool results and does not
  itself invoke `load_skill` or prove host execution.

### Versioned Lab artifact and build producer

- The tracked `plugins/skills-factory-lab/.codex-plugin/plugin.json` selects
  `plugins/skills-factory-lab/.mcp.json`, which launches the local
  `plugins/skills-factory-lab/mcp/server.py`. That checked-in release mirror
  is version `1.38.477` (`release-manifest.json` identifies release
  `1.38.477+d43250f3982f` in `plugins/skills-factory-lab/release-manifest.json`);
  its `plugins/skills-factory-lab/mcp/server.py` and
  `plugins/skills-factory-lab/mcp/skill_catalog.py` do not
  implement `expected_source_revision`. Its older SDK's behavior for an extra
  pin argument is not tested: it may reject or discard the unknown field, so
  this edge is `UNKNOWN`. Treat it as a stale, distinct artifact, not a third
  backend with the current pin contract. Whether any installed client still
  uses it is also `UNKNOWN`.
- A fresh package build takes the canonical server/catalog sources instead:
  `scripts/package/build_utils.py` copies `runtime/mcp/server.py` and
  `runtime/mcp/skill_catalog.py` into the Lab artifact. The build output uses
  the new contract when built from a source revision that contains it; this
  does not update the tracked `1.38.477` mirror or prove installation.
- `scripts/package/build_plugin.py` and `scripts/package/build_utils.py`
  generate local stdio, remote-HTTP, and skills-only plugin profiles. Local
  stdio bundles use the packaged Python server; the remote profile contains
  only an endpoint configuration, so support depends on that endpoint. The
  skills-only profile has no MCP runtime. Do not generalize one channel's
  contract to another installed artifact.

### Evaluation receipt consumers

- `scripts/eval/iteration02_flow_capture.py` checks observed provider calls,
  including a `load_skill` receipt, against the Site identity revision.
- `scripts/eval/iteration02_route_evidence.py` validates router and child
  `load_skill` receipt identity and explicitly rejects an inference that a
  loaded skill proves child model execution. These scripts consume evidence;
  they are not runtime tool callers.
- `scripts/eval/iteration02_site_native_receipt.py` validates Site-native
  receipt evidence. It is an evidence consumer, not a runtime caller.

### Build-time catalog producers

- `adapters/skills-factory-cloud-next/scripts/sync-lab-catalog.py` loads each
  packaged Lab entry to construct Site catalog metadata. That generator calls
  the package loader without `expected_source_revision`; it is build-time
  package inspection, not runtime adoption of the pin.
- `scripts/package/build_cloud_next_site.py` invokes that generator while
  building the Site. It is a producer in the packaging path, not a runtime
  `load_skill` client.
- `scripts/package/build_lab_plugin.py` builds the fresh Lab artifact and
  packages the canonical runtime/catalog sources; it is a package producer,
  not evidence that the tracked release mirror was refreshed or installed.
- `docs/catalog.json` supplies catalog metadata, including optional
  dependencies, which the generator returns with loaded entries. It is a
  content input to the catalog/package path, not an MCP caller.
- `workflows/runtime-registry.yaml` declares runtime workflow metadata, and
  `runtime/mcp/investment_runtime.py` supplies the runtime integration for
  investment workflows. These are workflow/runtime integration surfaces;
  their presence does not demonstrate optional-pin adoption by a caller.

### Source-evidence and evaluation inputs

- `scripts/eval/campaign.py` reads and hashes the ADR, adapter, catalog, tests,
  and other source evidence for campaign manifests. It is a source-evidence
  manifest consumer, not a `load_skill` runtime client.
- `evals/campaigns/iteration-07-investing-quality-2026-11/sdlc-source-compatibility-continuation.yaml`
  carries the Iteration-07 continuation inputs. It is evaluation configuration,
  not evidence of a direct tool call.
- `scripts/eval/promptfoo/promptfooconfig.yaml` configures a host probe that
  launches the stdio server and names `load_skill`. The prompt is a test input,
  not a direct runtime caller or proof of optional-pin adoption.
- `scripts/eval/prepare_closure.py` and `scripts/eval/release_bundle.py`
  prepare and validate evaluation/closure artifacts and prompts referring to
  runtime tools. They are evaluation producers/verifiers, not direct runtime
  callers.

These paths are source-confirmed at the pinned revision, but the inventory is
not a completeness proof. External HTTP/MCP clients and their optional-pin
adoption remain `UNKNOWN`; no source listing proves host execution of loaded
instructions or deployed API parity.

Pin adoption must be gated on the actual installed artifact's `tools/list`
schema and an observed stale-pin rejection against that same target. In
particular, do not send a pin to the tracked `1.38.477` artifact until it is
refreshed or its argument handling is tested; an ignored pin would defeat the
comparison.

## Migration, verification, and rollback

Existing callers need no migration. Callers that need source pinning may adopt
the field only after their actual installed artifact/channel supports it and
is discoverable; they must handle
the three source errors and must not interpret a successful unpinned call as a
pin. Python stdio and Cloud Next MCP contract tests cover omitted, matching,
malformed string and non-string pins, stale pins, malformed skill names,
unknown fields, and unverifiable package metadata; the Python test also
corrupts the package digest. The local raw MCP boundary verifies handler
behavior, but does not prove that every deployed connector preserves the
permissive schema. These are source-level checks, not live deployment evidence.
Undocumented consumers remain unknown; independent review and affected-channel
gates must be bound to the final candidate SHA.

There is no persisted-state migration. Before callers adopt the field, both
backends can revert to the one-field contract. After adoption, verify callers
have stopped sending it before reverting both schemas; if adoption cannot be
established, retain the contract and fix forward. Never silently ignore a
supplied pin. Rollback or publication does not follow from this decision alone.

## Historical worked-example baseline

This record retains the original pre-implementation source example because
the repository governance tests bind the architecture review to that exact
baseline. These entries describe the decision state before the later owner
approval and implementation below; they are not the current implementation
status.

- Baseline source SHA: `e0f613cbaf80cf4a278e713794662250dab2b8bc`
- Candidate SHA: `NOT_CREATED`.
- Status: `REVIEW_REQUIRED`.
- `ARCH-02` remains `NOT_RUN` at this historical baseline.

At that baseline, `runtime/contracts/mcp-tools-v1.json#L6-L8` required only
`skill_name`; `runtime/mcp/server.py#L297-L303` delegated that value to
`runtime/mcp/skill_catalog.py#L237-L272`; and
`adapters/skills-factory-cloud-next/src/cloud-tools.ts#L25-L29` plus
`#L182-L186` defined the second strict adapter. The Cloud Next declaration
was at `cloud-tools.ts#L128-L130`. Only these two source consumers were
confirmed; other callers remained `UNKNOWN`.

The original **Safe extension** kept the revision optional; the original
**Breaking alternative** made it required. The initial **Trust boundary**
prohibited using the caller value to select a path, URL, ref, or package.

## Rollback boundary

Before any caller sends `expected_source_revision`, both backends may revert
the optional field; after adoption, callers must stop sending the field before both
schemas are reverted; the server must never silently ignore a supplied field;
and the exact error shape for invalid or stale revisions remains owner-gated.
This was the original proposal state; the owner has since approved the stable
logical code/message contract documented above; byte-for-byte envelope parity
remains outside that approval.

## Successor source deltas for PR #800

PR [#800](https://github.com/aras-2003/skills-factory/pull/800) adds one
four-fixture, Cloud Next-only Investment OS pilot. This is an append-only
successor to the reviewed consumer map above. The code-source revision reviewed
for these deltas is `b41be28afdd34aea0330eb7f7a33284b85fda08d`; the final PR
candidate may add governance metadata and tests without changing these code
hashes. This does not revise the historical #766 decision, baseline, or
acceptance evidence. The exact allowed deltas to the 34 mapped consumer paths
are:

| Path | SHA-256 | Reason |
| --- | --- | --- |
| `runtime/contracts/mcp-tools-v1.json` | `972f2051373d3617d7d8229f1aeeaed7a23ecf960be87e09b7077a25b398d4b7` | Additive Cloud Next extension; shared `tools` contract remains unchanged. |
| `adapters/skills-factory-cloud-next/src/cloud-tools.ts` | `96a304438bb9f2ce59ce875220ffc43329efcb15f84a7f866aa42377ad155d81` | Register the fixture-only tool on authenticated MCP. |
| `sites/skills-factory-site/app/page.tsx` | `21999ae5739a635aca4877a2a2eb399707c8837c62596f8d6cadd6d7bbfed9cb` | Exclude the pilot from browser console and WebMCP discovery. |

The contract check asserts the `tools` map is semantically unchanged and
`load_skill` still requires only `skill_name`. Cloud Next MCP retains the
additive extension and receipt path. The browser page excludes this pilot from
its console and WebMCP registry; this does not claim the tool implementation
is absent from browser assets. The existing `242fe476` source-map commit stays
the historical ancestor and all other mapped source paths remain byte-identical.

The source-contract test harness also changes outside that 34-path map:
`adapters/skills-factory-cloud-next/scripts/check-contracts.mjs` is pinned in
the continuation manifest to SHA-256
`55591650298c304b8d5df8cd46390f8d2c1fff5b62264e67d360805380c2b699`. The
governance test allows only that exact harness digest refresh and verifies it
against the current file; it is not a fourth consumer-map delta.

The PR candidate must be independently reviewed against these three exact
hashes. After merge, a squash commit need not preserve the PR head as an
ancestor: validation remains anchored to `242fe476` plus the successor source
hashes and continuation manifest, not the ephemeral candidate commit ID.
