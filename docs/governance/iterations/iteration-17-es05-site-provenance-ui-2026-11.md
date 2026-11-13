# Iteration 17 — Skills Factory Site provenance UI and lineage (ES-05)

This record and its acceptance matrix define the complete scope for #620. Changes to frozen criteria require a separately reviewed clarification. Follow docs/governance/ITERATION-DELIVERY.md and the canonical Site publication runbook at docs/SITES-PUBLISHING.md.

- State: CLOSED / ACCEPTED; PR #669 merged; exact-source private runtime acceptance completed.
- Owner / reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review; not independent).
- Tracking issue / native Project iteration: #620 / not assigned; Project iteration is a scheduling mirror.
- Previous terminal iteration: Iteration 16 / #617 CLOSED / ACCEPTED; main SHA 87c2f736679a29c2ca228d806cc17d98bfc25879.
- Baseline main SHA: 87c2f736679a29c2ca228d806cc17d98bfc25879.
- Started / closed at (UTC): 2026-11-13 after scope-lock merge / 2026-11-13T16:47:52Z.
- Scope lock reviewed by / at: owner self-review / 2026-11-13.

## Frozen commitment

| Issue | Outcome / acceptance criterion IDs | Included | Excluded | Dependencies / evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #620 | 620-A1–A7 | Carry canonical provenance registry data into the generated Cloud Next catalog and list_skills response; add an accessible Site catalog browser with OWN, EXTENDED, IMPORTED, COMPOSED, UNKNOWN badges, filters by provenance/domain, search, and detail lineage including source identity, upstream pin, license/review state, local modifications and components; keep maturity, source status, declared/runtime channel availability and trust/license distinct; handle missing/unknown values without inference; verify exact source-to-catalog-to-Site-to-MCP parity and responsive desktop/mobile interactions; deploy the exact merged candidate to the existing owner-private Skills Factory Cloud Next Site using the official workflow. | No new provenance classifications or policy changes, automatic inference of ownership, import/adaptation/update automation (#618/#619), new Site or plugin identity, audience/access changes, production plugin package changes, production promotion, unrelated Site UX changes, or arbitrary Site mirror authoring. | #616 provenance schema and #617 secure intake accepted; canonical CATALOG.md, provenance/registry.yaml, docs/catalog.json generator, adapters/skills-factory-cloud-next, sites/skills-factory-site; runbook and native Sites workflow. | M |

## Design and data boundary

The canonical provenance registry remains the source of truth. Site/catalog data is generated from the same full Skills Factory commit as the Lab artifact, adapter bundle and source attestation. The provider-managed Site checkout remains a deployment mirror only. Do not hand-edit it.

Expose all five existing classifications exactly: OWN, EXTENDED, IMPORTED, COMPOSED and UNKNOWN. UNKNOWN is explicit and never becomes OWN by default. Provenance answers origin/lineage; license status, verification/trust state, maturity, source presence, declared channels and observed runtime availability remain separate fields. A classification alone never implies licensing approval, security clearance, maturity, package inclusion or runtime support.

Every displayed detail may contain source path and immutable source revision, upstream provider/url/path/commit/version/content digest where recorded, local modification state and explanation, license status/attribution, review state/date, component lineage and dependencies. Missing values render as UNKNOWN/NOT_RECORDED with no fabricated link, revision or license. Components are linked by canonical source identity and remain independently classified. User-visible labels explain these boundaries.

The catalog UI and MCP list_skills must read the same generated source-bound catalog. Search and filters are client-side and read-only. Source links target the exact canonical GitHub revision; external upstream links are shown only when canonical registry metadata contains a valid URI. No new data persistence or user tracking.

## Frozen acceptance criteria

- 620-A1 Data contract and parity: for every packaged Lab skill/workflow, generated Site catalog maps to the canonical source catalog by stable identity and carries all present provenance, license, source, modification, component, verification, maturity and channel fields; no mismatched or missing canonical source is silently accepted.
- 620-A2 Classification states: OWN, EXTENDED, IMPORTED, COMPOSED and UNKNOWN render distinct labels and filter values. UNKNOWN remains visible and is never inferred as OWN; missing metadata degrades explicitly.
- 620-A3 Details and orthogonality: detail view shows known source/upstream pin, license/review status, local modifications, components/dependencies and exact source SHA; provenance is visibly distinct from maturity, source status, runtime availability and trust/license review.
- 620-A4 Search and filters: search, provenance filter and domain filter compose correctly, keyboard-operable controls have labels, empty/reset states work, and counts represent the filtered catalog accurately.
- 620-A5 Responsive/accessibility: catalog and details render without horizontal page overflow at desktop and mobile widths; semantic headings, focus, contrast and accessible status text pass visual/manual checks.
- 620-A6 Site/MCP/runtime parity: Site UI, generated catalog and MCP list_skills return matching stable identities and provenance metadata from the exact candidate; runtime_info reports verified deployed identity, canonical source SHA and embedded Lab source SHA separately.
- 620-A7 Regression/deployment: existing Site MCP contracts, provenance/catalog validators, generated adapter freshness, source sync tests, TypeScript, lint/build and Domain Integrity pass. Official Sites workflow deploys only the exact merged source; actual Site version, mirror SHA and canonical/Lab SHAs are recorded independently. Audience and Site/plugin identity remain unchanged.

## Test plan

Authoritative ledger: evals/campaigns/iteration-17-es05-site-provenance-2026-11/acceptance-matrix.md. Rows begin NOT_RUN and must bind to one exact implementation source candidate. Required surfaces include canonical catalog projection, adapter catalog sync, MCP list_skills, UI search/filter/details, all provenance states, responsive/keyboard checks, generation freshness, Site/MCP runtime parity and exact deployed version. Run repository CI on every PR revision and applicable exact-main checks. Capture browser screenshots/interaction evidence at desktop and mobile sizes. Verify the live Site privately after deployment, explicitly record MCP runtime_info and list_skills calls, and distinguish canonical commit, provider mirror commit and embedded Lab commit. No production plugin promotion is in scope.

## Candidate history (append; never overwrite)

| Candidate | Main SHA | Site version / deployment | Build + CI | Observed Site/MCP identity and UI evidence | Supersedes / invalidated rows |
| --- | --- | --- | --- | --- | --- |
| Scope baseline | 87c2f736679a29c2ca228d806cc17d98bfc25879 | Site v132 before publication | Scope-lock PR #668 merged; implementation candidate #669 validated | Baseline only | None |
| Accepted candidate | 197f12e96a2282eb13cf787246e76e3621c960eb | Site v133; deployment appgdep_6af73cad04ac8191990a27864dd0a7f0; mirror b0216d283dad3fd297b6e3a64293a4434b8245f6 | Candidate CI #1391/#642 and exact-main Validate #1392/Site CI #643 passed; local tsc/lint/build passed | Runtime info verified; list_skills returned 98 rows / release 1.38.526+197f12e96a22; desktop and mobile interactions observed | Scope-lock SHA 483f78b; implementation PR #669 |

## Regression selection

- Direct consumers: provenance projection, docs/catalog.json, Cloud Next generated skill-catalog.ts, list_skills output, Site catalog UI and source sync.
- Included / excluded: all 17 matrix rows; all five classifications, missing metadata, catalog/MCP parity, desktop/mobile interactions, official private Site deployment. Excludes #618/#619 behavior and production plugin promotion.
- Fixed sentinels: unknown never OWN; imported never means production-ready; canonical/Lab/mirror identities are distinct; no stale Site catalog.
- Unchanged-domain probes: two existing skill/workflow contract checks selected before final validation.
- Repeats: deterministic catalog generation and filter contracts run twice; UI browser checks cover desktop and mobile once per exact candidate with repeat captures after fixes.
- External runtime: private owner-only Cloud Next Site only; production plugin channel remains unchanged.

## Defect intake and clarifications (append)

| Issue / discovery | Existing contract or unrelated | Severity / blocks closure | Fix / deferral | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |
| None at scope lock | Baseline reviewed | N/A | N/A | N/A | Owner |

## Closure / abort decision

- Outcome: CLOSED / ACCEPTED.
- Final implementation source SHA: 197f12e96a2282eb13cf787246e76e3621c960eb; Site mirror SHA: b0216d283dad3fd297b6e3a64293a4434b8245f6; embedded Lab SHA: 197f12e96a2282eb13cf787246e76e3621c960eb.
- Matrix: evals/campaigns/iteration-17-es05-site-provenance-2026-11/acceptance-matrix.md; 17 PASS, 0 FAIL, 0 NOT_RUN, 0 BLOCKED/REVIEW_REQUIRED, 0 reviewed N/A.
- Shared regression verdict: PASS; candidate Domain Integrity #1391, Site CI #642, exact-main Validate skills #1392 and Site CI #643 passed; local TypeScript/lint/build passed.
- Site version/deployment: v133; deployment appgdep_6af73cad04ac8191990a27864dd0a7f0 succeeded at 2026-11-13T16:37:42Z; owner-only access confirmed; archive sha256 0699e27e4e4ab6e3a7e81b31b392cea3cb794639e2377b0b9935ffb6a5d3614c.
- Scope compared with lock: no deviations; actual catalog's 98 classifications remain UNKNOWN where evidence is absent; no automatic ownership inference.
- Issue / PR reconciliation: #620 closed after successful implementation/runtime acceptance; PR #669 merged.
- Owner proposal / reviewer acceptance / timestamp: owner self-review; independent review not claimed; acceptance recorded 2026-11-13T16:47:52Z.
- Next iteration eligibility: #618 is eligible after terminal #620; #616/#617 are terminal. No automatic production promotion.
