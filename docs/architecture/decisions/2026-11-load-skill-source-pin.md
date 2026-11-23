# `load_skill` source-pin decision

- Issue: [#766 — Software architecture decision and contract-review capability for A2–A4](https://github.com/aras-2003/skills-factory/issues/766)
- Criteria: AC-02, AC-03, ARCH-02, ARCH-03, ARCH-05, ARCH-07
- Architecture Impact: A2 proposed for the shared tool contract; native project field not independently verified.
- Decision: owner approved the optional source pin and the invalid and mismatch errors. The fail-closed unverifiable error is an engineering assumption, not an additional owner-approved case.
- Baseline source SHA: `1bc7677b6c63427a20b3e9f2595dce797905542b`.
- Candidate SHA: pending commit. This is source-only work; no publication, live runtime acceptance, or independent exact-SHA review is claimed here.

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

## Source-grounded consumer map

- Python MCP registers and dispatches `load_skill` in
  `runtime/mcp/server.py`, then reads the packaged catalog through
  `runtime/mcp/skill_catalog.py`.
- Cloud Next handles MCP calls in
  `adapters/skills-factory-cloud-next/src/mcp-handler.ts`, dispatches through
  `adapters/skills-factory-cloud-next/src/cloud-tools.ts`, and loads the
  generated embedded `skill-catalog.ts` (created by
  `adapters/skills-factory-cloud-next/scripts/sync-lab-catalog.py`).
- These are source-confirmed adapter paths, not a complete external-client
  inventory. Other consumers and their adoption state remain `UNKNOWN`.

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
