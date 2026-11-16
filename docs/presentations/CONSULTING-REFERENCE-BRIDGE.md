# Consulting reference → Presentation OS semantic bridge (first implementation slice)

## Why
The previous CIO example generated technically openable but visually weak artifacts. A renderer/valid JSON alone cannot prove consulting-grade quality. This slice reuses the *verified historical source register* rather than re-auditing seven ZIPs or copying external text/code. References are **not** official McKinsey/BCG outputs; none of the community repos implies brand affiliation. Sources without redistributable permissions are reference-only.

## Actual implementation
- `consulting-reference-patterns-v1.json` holds pinned sources, license boundaries, six original slide-composition principles.
- `scripts/presentations/reference_style_bridge.py` maps canonical DeckSpec v1 `slide_id`, `role`, `claims` into a deterministic, inspectable layout plan with explicit reference IDs and revisions.
- `tests/presentations/test_reference_style_bridge.py` tests positive, no-pattern, missing-claim, contradicted-claim, duplicate-ID, invalid-status paths.
- Produces *only a semantic plan*: explicitly emits `render_status: NOT_RUN`, `editable_export_status: NOT_RUN`. It neither calls external skills nor imports unapproved helpers.
- No changes to the canonical deck schema, renderer, skill packaging or production channel.

## Usage
```bash
python -m unittest discover -s tests/presentations -p 'test_reference_style_bridge.py'
python scripts/presentations/reference_style_bridge.py path/to/canonical-deck.json --out /tmp/reference-plan.json
```

The `role` can be one of: `decision`, `options`, `capability`, `architecture`, `roadmap`, `kpi`. Unsupported roles yield NO_PATTERN rather than a fabricated style match. Claims with unknown status or malformed IDs are rejected; missing or contradicted evidence blocks confident selection.

## Known gaps and next gates
1. The design principles are independently authored hypotheses informed by the *repository-level audited corpus*. **They have not been extracted via a newly executed page-by-page visual examination**; therefore they do not constitute a validated BCG/McKinsey/Accenture slide benchmark.
2. Secure intake and execution of `openai/skills` slides candidate remains BLOCKED in #621; Marp Uncover remains only a candidate. This bridge does **not** call either.
3. Native PPTX rendering, visual comparison, geometry, editor roundtrip, repeatability across runtimes and human review remain NOT_RUN for this increment.
4. Next scope: validate pattern use against real exhibits from official public company reports, integrate into existing #611 theme and #612 exhibit pipeline, render 10-slide CIO golden fixture and run independent visual QA under #613. Do not claim end-to-end quality PASS until that occurs.

## Traceability
Source evidence: #450 / PR #508; external presentation candidates and intake blocker #621; parent Presentation OS #283; renderer reuse #608; theme #611; assets #612; cross-format QA #613; architecture IR #739.

**Acceptance in this change:** semantic plan and source-lineage implementation delivered; test execution CI/host to verify; real deck/visual score NOT_RUN.

## PRES-09 implementation addendum (2026-11-16)
- **18 registered references**: seven archive-level Strategy OS sources with historical SHA, two separately pinned OpenAI/Marp candidates, and nine publicly accessible official BCG/McKinsey/Accenture HTML publications (three per firm). The official sources are recorded with source anchors and abstract editorial observations; source pages are *not* copied.
- **Ten originally authored patterns**: decision, options, capability, architecture, governance, roadmap, KPI, risks, value, handoff. Each records source IDs and intended communication outcome; these are not firm-branded templates or certified consulting methods.
- **CIO 10-slide fixture**: `docs/presentations/examples/cio-reference-golden-v1.json` keeps user-supplied baseline separate from proposed hypotheses. `reference_style_bridge.py` emits exact `slide_id → layout_id → source_id → source rights/revision/anchor` consumption record.
- **Regressions**: ten unit tests cover evidence uncertainty, full fixture lineage, source-ID collisions, unknown references, rights coverage, duplicate slides and missing patterns. A dedicated read-only GitHub Actions job runs these and generates the fixture plan.
- **Rights:** external community methods are historical reference sources, not officially affiliated consulting-firm assets; five unlicensed ZIPs are reference-only; MIT and Apache packages still require their own notice obligations if ever copied. `openai/skills` secure-intake remains blocked in #621 and must not be bypassed.
- **Evidence categories:** source publication/section checked via public HTML; page screenshot/layout inspected = **NOT_RUN**; independent visual benchmark = **NOT_RUN**; native PPTX = **NOT_RUN**. This implementation can establish source-informed **semantic layout selection**, not executive-grade rendering.

## Acceptance and follow-up
| PRES-09 criterion | Current evidence | Result |
|---|---|---|
| Reuse #450 source archive register | Historical hashes, provenance and rights inherited without copying ZIPs | PASS: manifest-linked |
| 3 official sources per firm | Nine public HTML links with anchors and original observations | PASS: editorial/source coverage; visual inspection NOT_RUN |
| At least 8 original patterns | Ten roles with source links | PASS: registry |
| Fixture demonstrates actual pattern consumption | CLI adapter + ten-slide canonical fixture + tests | CI pending / runtime NOT_RUN until green receipt |
| Independent design reviewer | No reviewer assigned | NOT_RUN |
| Quantified baseline vs improved visual output | No paired render/quality scores yet | NOT_RUN |
| Third-party skill execution | OpenAI Slides intake blocked; no third-party execution claimed | BLOCKED |
| Release into Presentation OS renderer | Intentionally not integrated with renderer | NOT_RUN |

**Release decision:** do not mark #744 Done while visual inspection, review and baseline/candidate measurement remain missing. The adapter is a bounded proof of consumption, not the complete consulting-grade style system.
