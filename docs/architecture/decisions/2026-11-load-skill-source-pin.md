# `load_skill` source-pin decision example

> This is a worked architecture example for issue #766, not an approved API
> change. It evaluates a backward-compatible option against a breaking option
> using the current repository contract.

## Decision identity

- Issue: [#766 — Software architecture decision and contract-review capability for A2–A4](https://github.com/aras-2003/skills-factory/issues/766)
- Numbered criteria: AC-02, AC-03, ARCH-02, ARCH-03, ARCH-05, ARCH-07
- Architecture Impact: A2 (proposed for a shared public tool contract; project field not independently verified)
- Status: `REVIEW_REQUIRED`
- Baseline source SHA: `e0f613cbaf80cf4a278e713794662250dab2b8bc`
- Candidate SHA: `NOT_CREATED` — this record does not authorize implementation or release.
- Decision owner / independent reviewer: owner / `NOT_REVIEWED`

## Context and source-backed consumers

The canonical tool contract declares `load_skill` with one required input,
`skill_name`, in `runtime/contracts/mcp-tools-v1.json#L6-L8`. The Python MCP
server delegates that value to `runtime/mcp/skill_catalog.py`, which validates
the name and reads instructions from the packaged Lab catalog
(`runtime/mcp/server.py#L297-L303`, `runtime/mcp/skill_catalog.py#L237-L272`).
The Cloud Next adapter has a separate strict Zod tool schema and loader
(`adapters/skills-factory-cloud-next/src/cloud-tools.ts#L25-L29`,
`#L182-L186`). These are two source-confirmed runtime consumers of the same
logical interface. The Cloud Next tool declaration also exposes the current
MCP input schema (`cloud-tools.ts#L128-L130`).

Both loaders return the packaged canonical `source_revision`. Neither accepts
an expected revision from a caller, so a caller can check the result after
loading but cannot ask the tool to reject a stale package before returning the
instructions. The Lab provenance is package data; the provider Site commit is
a separate revision and must not be substituted for it.

## Options and recommendation

**Safe extension:** add an optional `expected_source_revision` string to the
input. Omission preserves current v1 calls. When supplied, each implementation
first validates a lowercase 40-character hexadecimal SHA, compares it to the
packaged canonical source revision, and returns a typed stale-source error on
mismatch before loading content. The parameter is a comparison value only: it
must not select a Git ref, filesystem path, URL, or remote package. Existing
strict-object behavior remains in place for unknown fields.

**Breaking alternative:** make `expected_source_revision` required. Existing
Python MCP clients, Cloud Next callers, and workflow instructions only send
`skill_name`; they would fail validation until every caller and host schema is
updated together. A synchronized breaking change would need a new contract
version or a separately approved migration window. No current evidence
requires that break.

**Recommendation:** if source pinning is implemented, use the optional
extension and retain the current omitted-field behavior. Do not implement it
until the two backends have parity tests and the owner accepts the error shape.
This is design guidance, not authorization to change the MCP contract.

## Trust boundary, tests, and recovery

The caller-provided SHA is untrusted input. Strict format validation and exact
equality against packaged provenance avoid path traversal and remote access.
The check must use canonical Lab provenance, not Site mirror history. It must
not expose evaluator fixtures, credentials, or permission data. No new tool
permission is required.

| Case | Expected behavior | Evidence required before acceptance |
| --- | --- | --- |
| `ARCH-02-A` | Existing `{skill_name}` call remains valid and returns the same packaged skill. | Python and TypeScript compatibility tests. |
| `ARCH-02-B` | Matching optional SHA succeeds. | Python and TypeScript exact-source tests. |
| `ARCH-02-C` | Malformed or stale SHA fails before instruction content is returned. | Negative tests in both backends, with output redaction checked. |
| `ARCH-02-D` | Unknown fields remain rejected. | MCP schema/strict-object tests. |
| `ARCH-03` | Any undocumented consumer remains `UNKNOWN`; test selection retains the full affected-channel baseline. | Source-pinned consumer review and `change_gate.py` output. |
| `ARCH-05` | A changed baseline or material contract diff invalidates this record. | Independent review bound to the new candidate SHA. |

There is no persisted state migration. Rollback is to remove the optional
field handling and restore the existing one-field schema; clients that omitted
the optional value continue to work. If the error shape or provenance source
cannot be made identical across both backends, stop before merge and keep the
current contract.

## Review state

This example is pinned to the source used for analysis, but has no candidate
implementation or independent approval. `ARCH-02` remains `NOT_RUN` and the
decision remains `REVIEW_REQUIRED` until a real candidate, paired backend
tests, and independent exact-SHA review exist.
