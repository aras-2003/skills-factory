# `load_skill` source-pin decision

- Issue: [#766 — Software architecture decision and contract-review capability for A2–A4](https://github.com/aras-2003/skills-factory/issues/766)
- Criteria: AC-02, AC-03, ARCH-02, ARCH-03, ARCH-05, ARCH-07
- Architecture Impact: A2 proposed for the shared tool contract; native project field not independently verified.
- Decision: owner approved the optional source pin and the invalid and mismatch errors. The fail-closed unverifiable error is an engineering assumption, not an additional owner-approved case.
- Implementation baseline SHA: `1bc7677b6c63427a20b3e9f2595dce797905542b`.
- Implementation candidate SHA: `5cedbb5354913b9299818c048400b72a976fff17`.
- Review status: source-only checks pass; exact-SHA review and publication/runtime acceptance remain separate gates.

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
This unsigned manifest and digest demonstrate payload consistency, **not
origin authentication or deployment attestation**. Cloud Next uses the
embedded Lab release revision, generated from a digest-checked Lab package;
the Site deployment mirror revision is a separate identity. Neither check
establishes execution by a host model.

Requiring the field was considered and rejected: existing clients send only
`skill_name`, and making it mandatory would require a coordinated versioned
migration without evidence of a need for that break.

## Current source consumer map

This map was checked against the main tree at `02001acb4269cb74b4a3e39f095fe027663c21eb`.
It separates runtime tool consumers from receipt validators and build-time
catalog producers; finding a path does not imply that it sends the optional
`expected_source_revision` pin.

## Reuse decision

`REUSE` the existing repository method in
`docs/architecture/SOFTWARE-ARCHITECTURE-DECISIONS.md` and
`templates/architecture/software-decision.md`. This worked example strengthens
that method with a source-confirmed consumer map; it does not introduce a
separate software-architecture skill or duplicate approval workflow. Reconsider
a reusable skill only if repeated cross-repository use demonstrates a distinct
method from the existing enterprise architecture and skill-specification
capabilities.

### Runtime and transport consumers

- Python MCP registers `load_skill` in `runtime/mcp/server.py` and reads the
  packaged catalog through `runtime/mcp/skill_catalog.py`. The compatibility
  HTTP entry point `runtime/mcp/cloud_server.py` imports the same server and
  starts Streamable HTTP; it is not a second implementation.
- Cloud Next receives MCP requests in
  `adapters/skills-factory-cloud-next/src/mcp-handler.ts`, validates and
  dispatches them through `adapters/skills-factory-cloud-next/src/cloud-tools.ts`,
  and loads the generated embedded catalog. The Site `/mcp` route in
  `sites/skills-factory-site/app/mcp/route.ts` delegates POST/GET/DELETE to
  that handler.
- The Site browser surface in `sites/skills-factory-site/app/page.tsx` imports
  `callTool`; its WebMCP `document.modelContext.registerTool` callback and the
  interactive console both call that adapter. Its sample `load_skill` request
  sends `skill_name` only, so it does not demonstrate pin adoption.

### Evaluation receipt consumers

- `scripts/eval/iteration02_flow_capture.py` checks observed provider calls,
  including a `load_skill` receipt, against the Site identity revision.
- `scripts/eval/iteration02_route_evidence.py` validates router and child
  `load_skill` receipt identity and explicitly rejects an inference that a
  loaded skill proves child model execution. These scripts consume evidence;
  they are not runtime tool callers.

### Build-time catalog producers

- `adapters/skills-factory-cloud-next/scripts/sync-lab-catalog.py` loads each
  packaged Lab entry to construct Site catalog metadata. That generator calls
  the package loader without `expected_source_revision`; it is build-time
  package inspection, not runtime adoption of the pin.
- `scripts/package/build_cloud_next_site.py` invokes that generator while
  building the Site. It is a producer in the packaging path, not a runtime
  `load_skill` client.

These paths are source-confirmed on the stated revision, not a complete
consumer inventory. External HTTP/MCP clients and their optional-pin adoption
remain `UNKNOWN`; no source listing proves host execution of loaded
instructions or deployed API parity.

## Migration, verification, and rollback

Existing callers need no migration. Callers that need source pinning may adopt
the field after both adapters are available and discoverable; they must handle
the three source errors and must not interpret a successful unpinned call as a
pin. Python stdio and Cloud Next MCP contract tests cover omitted, matching,
malformed, stale, and unknown inputs; the Python test also corrupts the
package digest. These are source-level checks, not live deployment evidence.
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
