# ARC-01 — Archify technical spike (preliminary)

Issue: #374 | Iteration: #373 | Status: development / gated by actual GitHub Actions receipts

## Evidence checked
Upstream: https://github.com/tt-a1i/archify, stable tag `v3.2.0`. Inspected tag files `LICENSE`, `package.json`, `archify/SKILL.md`, and example `archify/examples/web-app.architecture.json` through connected GitHub read operations (2026-10-22). License: MIT; retain license and copyright notices if distributing a copied implementation. Root package engines: Node >=18. Dev dependencies include ajv, parse5, saxes, skills and yaml; nested runtime dependencies require separate review.

**Immutable pin verified:** upstream release tag `v3.2.0` resolves to commit `208acba8d412335185b2056fedf54b3405df43fb`; nested `archify/package-lock.json` has Git blob `e6187b907edc8459f47fe31455539700f2d8e796`. Both are checked at runtime in `ci-archify-spike.yml`; see `ARCHIFY-UPSTREAM-LOCK.json`. GitHub-hosted `npm audit --audit-level=high` returned no high or critical findings, but reported **one moderate vulnerability** `fast-uri` 3.1.7, advisory `GHSA-hrr3-gc8f-f4qj` (observed GitHub run 39872544806). This is a supply-chain exception requiring an explicit risk decision before production integration; do not silently patch the upstream release. Do not install `npx skills add -g` inside CI or developer machines automatically. No upstream code is vendored in this spike.

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
3. **HIGH — supply chain:** immutable pin established; pinned nested dependency `fast-uri` 3.1.7 has a moderate advisory. Production adoption requires reviewed mitigation or risk acceptance and must never run untrusted code with privileged credentials.
4. **MEDIUM — side effects:** forbid global install, automatic update, network calls, unexpected output paths and uncontrolled subprocess execution.
5. **MEDIUM — export semantics:** SVG/PNG/WebM/PDF and native PPTX editability must be tested independently; image export is not editable shape export.

## PoC contract
The source-controlled fixture at `fixtures/synthetic-architecture.json` is intentionally fictional. It has exactly three nodes and two directed relationships. `scripts/check_fixture.py` checks exact structure, edge referential integrity, prohibited active content and stable SHA-256. This is ONLY pre-render fixture validation. It does not substitute for actual Archify finalize and browser checks.

### Commands for an isolated developer environment
1. Obtain upstream at **commit `208acba8d412335185b2056fedf54b3405df43fb`**, not a mutable tag. Record SHA and verify provenance; no global installation.
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
| Immutable upstream SHA pin | PASS — pinned commit and lockfile Git blob in CI |
| Local fixture check | PASS — GitHub Actions input and adversarial tests |
| Actual Archify finalize/browser/export | NOT_RUN |
| Security/advisory audit | PASS for high/critical; residual moderate `fast-uri` finding requires explicit production risk decision |
| Distribution and runtime integration | NOT_RUN |

**Decision:** no release/merge readiness claim. ARC-02 and following are outside this issue.

## CI / scope clarification

The new `ci-archify-spike.yml` workflow executes pinned upstream in a disposable GitHub runner with no repository credentials persisted by checkout. Dependency installation requires internet; `ARCHIFY_UPDATE_CHECK_DISABLED=1` prevents Archify's update awareness call during CLI execution. **This does not prove that the CLI subprocess has OS-enforced network isolation**; true `--network=none` or equivalent must be provided before any non-synthetic or privileged deployment. This spike only tests synthetic input and must not publish active HTML under a privileged origin. Static input filtering rejects raw HTML, active URLs and arbitrary output paths; this does not constitute general sanitization of untrusted diagrams.

Current export contract: self-contained interactive HTML is a candidate after finalize/browser-check PASS. Any SVG/PNG/WebM export and native editable PowerPoint shapes remain UNVERIFIED unless separately exercised; this PoC does not promise such interoperability.
