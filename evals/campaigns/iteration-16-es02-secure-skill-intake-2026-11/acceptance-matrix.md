# Iteration 16 / ES-02 secure external skill intake acceptance matrix

Scope-lock ledger for #617. Every result begins NOT_RUN and must bind to the same exact implementation candidate. This tooling-only increment does not change a skill, runtime MCP contract, Site, or production package.

| Row | Criterion | Surface / case | Planned evidence and pass condition | Candidate / artifact identity | Status |
| --- | --- | --- | --- | --- | --- |
| 16-01 | 617-A1 | Local directory intake: safe synthetic skill | Complete normalized inventory; deterministic file order, bytes and SHA-256; no source mutation. | pending | NOT_RUN |
| 16-02 | 617-A1 | Local ZIP bundle intake: safe synthetic skill | Read members without unsafe extraction; equivalent logical file inventory and per-file hashes; receipt identifies bundle digest. | pending | NOT_RUN |
| 16-03 | 617-A1 | Remote repository intake: pinned synthetic transport | Accept only HTTPS provider URL + immutable full commit; transport mocked in offline tests; capture repo, commit, author metadata when verified, and source archive digest. | pending | NOT_RUN |
| 16-04 | 617-A2 | Mutable/ambiguous remote refs | Branch, tag, shortened SHA, redirect to untrusted host, and missing repository identity are refused; no network request occurs for malformed input. | pending | NOT_RUN |
| 16-05 | 617-A2 | Receipt and pinned manifest reproducibility | Two runs over unchanged bytes produce byte-identical canonical receipt/manifest; every member has a SHA-256; invalid/malformed pins fail closed. | pending | NOT_RUN |
| 16-06 | 617-A2 | Upstream content drift | Review authorization binds repository, immutable commit and complete inventory digest; any changed commit or file digest invalidates it and returns NOT_AUTHORIZED. | pending | NOT_RUN |
| 16-07 | 617-A3 | No-execution / side-effect fixture | Hostile scripts, lifecycle hooks and prompt-injection text remain inert data; no subprocess, import, outbound request, production write or protected-source mutation occurs during discovery. | pending | NOT_RUN |
| 16-08 | 617-A4 | Threat inventory and static review signals | Fixtures cover secret exfiltration, permission expansion, destructive commands, dependency confusion, unexpected network/write behavior and embedded assets; findings remain review signals, never execution or automatic trust. | pending | NOT_RUN |
| 16-09 | 617-A5 | License and author provenance decisions | APPROVED, REVIEW_REQUIRED, REJECTED and UNKNOWN parse as distinct explicit decisions; presence of LICENSE/author text never auto-approves; missing/unverified claims remain UNKNOWN or REVIEW_REQUIRED. | pending | NOT_RUN |
| 16-10 | 617-A5 | Duplicate and reviewer gate | Exact source/content duplicates are deterministically identified; ambiguous similarity is review-only; no import-ready state without an explicit review bound to the exact receipt digest. | pending | NOT_RUN |
| 16-11 | 617-A6 | Hostile archive and path cases | Reject absolute paths, traversal, backslash aliases, duplicate normalized paths, symlink/hardlink entries, encrypted members, malformed archives, excessive file/member/expanded-size limits and compression bombs; create no escaped files. | pending | NOT_RUN |
| 16-12 | 617-A6 | Missing, malformed and hostile skill metadata | Missing SKILL.md, invalid UTF-8/frontmatter, suspicious tool/permission requests, hidden prompt instructions and unsupported resource types produce refusal/review state with bounded diagnostics. | pending | NOT_RUN |
| 16-13 | 617-A7 | Existing security/provenance/package consumers | Security scanner, provenance schema/validators, repository validation, packaging and Domain Integrity remain green; no maturity, channel, security, license, production or catalog state is silently elevated. | pending | NOT_RUN |
| 16-14 | iteration | Shared identity/invocation smoke | Exact candidate CLI help and one synthetic safe intake invocation return schema-valid, digest-bound output; record command, candidate SHA and output hash. | pending | NOT_RUN |
| 16-15 | iteration | Shared authorization/evidence/output sentinels | Explicitly verify no side effect without authorization, receipt digest integrity, deterministic output, preserved existing source/catalog/package contracts, and one unchanged critical security scan path. | pending | NOT_RUN |
| 16-16 | iteration | Rotating unchanged-domain probes | Choose and run two unchanged skill/workflow validation probes before final checks; retain commands and output hashes. | pending | NOT_RUN |

## N/A declared at scope lock

- Site MCP/Chat semantic runtime, visual UI and production runtime: N/A because the locked change is a repository-side intake command/library and does not alter any skill behavior, Site surface, or deployed package. This rationale must be rechecked against the final diff; if scope changes, stop and add required runtime rows before proceeding.
- External production imports, automatic promotion, automatic license approval, skill adaptation, overlap matching, upstream update automation, rollback, and domain adoption are excluded and remain unclaimed.
- Real internet downloads are not part of deterministic CI. Remote transport behavior is tested through a controlled mock with redirects, host validation, size limits, and errors; one optional manual public-source smoke may be recorded only against a reviewed immutable test fixture, never an arbitrary source.

## Completeness and close gate

All frozen criteria must map to passing rows on the final candidate. Preserve each failed attempt. Required FAIL, NOT_RUN, BLOCKED or REVIEW_REQUIRED rows prevent closure unless a criterion has an explicit, reviewed disposition allowed by the repository policy. Verify canonical receipt and manifest schemas, exact source/file hashes, bounded archive handling, and absence of unauthorized side effects. The matrix is an index; retain detailed test logs and command receipts.