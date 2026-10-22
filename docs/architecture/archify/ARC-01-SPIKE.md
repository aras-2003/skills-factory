# ARC-01 — Archify technical spike (preliminary)

Issue: #374 | Iteration: #373 | Status: PARTIAL / validation NOT_RUN

## Evidence checked
Upstream: https://github.com/tt-a1i/archify, stable tag `v3.2.0`. Inspected tag files `LICENSE`, `package.json`, `archify/SKILL.md`, and example `archify/examples/web-app.architecture.json` through connected GitHub read operations (2026-10-22). License: MIT; retain license and copyright notices if distributing a copied implementation. Root package engines: Node >=18. Dev dependencies include ajv, parse5, saxes, skills and yaml; nested runtime dependencies require separate review.

**Important:** the Git tag is NOT an immutable SHA pin. Before approving dependency integration, resolve and record the tag target commit SHA and content digest from an authenticated source, audit transitive dependencies, check security advisories and confirm licensing of bundled assets. Do not install `npx skills add -g` inside CI or developer machines automatically. No upstream code is vendored in this spike.

## Technical findings
- Native diagram types include architecture, workflow, sequence, dataflow, lifecycle, ERD, class, tree, timeline and waterfall.
- Authoring uses JSON; architecture fixture schema_version=1 with components, connections and optional boundaries/cards.
- Recommended upstream invocation: `node bin/archify.mjs finalize architecture <candidate.json> <output.html> --quality showcase --json`; `--repo-root` is relevant to source-backed evidence.
- Finalize combines validation, delivery, strict check and browser-check per upstream documentation. An upstream claim is not local execution evidence.
- HTML viewer is interactive; other exports need actual format-specific verification before claiming parity.
- Update checking can be disabled with `ARCHIFY_UPDATE_CHECK_DISABLED=1`; enforce no outbound network in the PoC runner.

## Risk register / acceptance blockers
1. **HIGH — untrusted active HTML:** never host arbitrary generated HTML on the same origin as private Site/session data. Sandbox with separate origin and strict CSP, disallow access to credentials and privileged tools. Test escaping and malicious URL handling.
2. **HIGH — source provenance:** no model relation may be created purely from renderer layout or examples. Synthetic fixture is clearly marked synthetic; upstream source-backed check does not validate business facts.
3. **HIGH — supply chain:** unpinned mutable tag and incomplete dependency audit mean no production adoption.
4. **MEDIUM — side effects:** forbid global install, automatic update, network calls, unexpected output paths and uncontrolled subprocess execution.
5. **MEDIUM — export semantics:** SVG/PNG/WebM/PDF and native PPTX editability must be tested independently; image export is not editable shape export.

## PoC contract
The source-controlled fixture at `fixtures/synthetic-architecture.json` is intentionally fictional. It has exactly three nodes and two directed relationships. `scripts/check_fixture.py` checks exact structure, edge referential integrity, prohibited active content and stable SHA-256. This is ONLY pre-render fixture validation. It does not substitute for actual Archify finalize and browser checks.

### Commands for an isolated developer environment
1. Obtain upstream source at **resolved immutable commit SHA** corresponding to reviewed release. Record SHA and verify provenance; no global installation.
2. `python3 docs/architecture/archify/scripts/check_fixture.py`
3. Copy fixture to an isolated writable directory; update `meta.output` to an output path inside that directory, if required by installed version.
4. With outbound network disabled and `ARCHIFY_UPDATE_CHECK_DISABLED=1`, run `node <checked-upstream>/archify/bin/archify.mjs finalize architecture <fixture> <output.html> --quality showcase --json` (verify CLI entry path in pinned checkout).
5. Run browser-check against the exact output; inspect active HTML, CSP constraints and export menu. Keep receipts and SHA-256 of artifact.
6. Run malicious text/URL and failure tests in the same sandbox, and log precise PASS/FAIL/NOT_RUN per gate.

## Evidence ledger
| Gate | Status |
|---|---|
| Repository and license inspected | PASS (static review) |
| Example fixture authored | PASS (source committed) |
| Immutable upstream SHA pin | NOT_RUN |
| Local fixture check | NOT_RUN in connected GitHub environment |
| Actual Archify finalize/browser/export | NOT_RUN |
| Security/advisory audit | NOT_RUN |
| Distribution and runtime integration | NOT_RUN |

**Decision:** no release/merge readiness claim. ARC-02 and following are outside this issue.
