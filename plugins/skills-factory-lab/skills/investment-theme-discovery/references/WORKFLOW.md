# Investment Theme Discovery Workflow

## Purpose
Research a structural or cyclical trend, map where economics accrue and create an XTB-focused research queue without equating narrative strength with investability.

## Entry criteria
Enter for a bounded thesis about a structural/cyclical mechanism, value-chain economics, beneficiary exposures and research candidates. A single issuer or portfolio sizing request belongs to a specialist.
Default to **read-only discovery**. A request to investigate or produce a watchlist is not authorization to persist. Require a verified canonical baseline if stating a theme changed versus its previous version.

## Required skills
- trend-theme-research
- market-opportunity-scan
- investment-record-store

## Optional skills
- investor-pattern-research
- security-underwriting
- thesis-challenge

## Sequence
1. Read prior canonical theme versions and related signals.
2. Define mechanism and horizon; separate secular, cyclical and narrative components.
3. Use structured equity/thematic research plugins for breadth and candidate/value-chain discovery.
4. Use Firecrawl/primary sources to verify material bottleneck, demand, capacity and economic-capture claims.
5. Map value chain, bottlenecks, leading indicators, beneficiaries, losers and invalidation.
6. Compare new evidence with prior theme state.
7. Intersect candidate beneficiaries with the XTB-investable universe.
8. Run market-opportunity-scan to identify favorable security-level setup rather than theme exposure alone.
9. Determine persistence permission separately. If the user has not explicitly authorized append to an identified canonical TEST/production target (or a separately verified standing policy), do not write; report NOT_WRITTEN and preserve output in the conversation only. Preview, analysis, read-only and unknown-permission contexts must never inherit previous write consent.
10. For an authorized operation only, append a new theme version/sources/candidates via investment-record-store without rewriting history. Return SAVED solely with a verified canonical WRITE receipt containing identity/time; if the operation fails, return WRITE_FAILED. Theme activation or an investment decision needs its own separate authorization.
11. Underwrite only the few candidates where theme economics and security setup justify deeper work.

## Decision rules
- demand growth can coexist with bad supplier economics;
- second-order beneficiary claims require evidence of value capture;
- thematic-provider output is discovery evidence, not canonical state;
- theme discovery never issues position sizes;
- external-write permission is distinct from canonical read permission and from an analytical request.

## Output contract
Theme mechanism | changes since prior view | indicators | value chain | beneficiaries/losers | crowded assumptions | invalidation | XTB research queue | provenance | persistence receipt.

## Stop conditions
Stop once a falsifiable theme map and bounded research queue exist.
If canonical data/permissions are missing, do not fabricate a prior theme or saved version; give provisional analysis and NOT_WRITTEN. No background persistence or unconditional side effects.

## Integrated report presentation
Render the report directly in the chat response by default. External HTML/PDF/Figma/deck/file output is allowed only when the user explicitly requests that artifact or format.

After synthesis, call `report-composer`.

Default profile:
- theme mechanism with inline value-chain/mechanism diagram;
- leading indicators;
- beneficiaries and losers;
- candidate-security sections with local evidence/price context where useful;
- invalidation;
- research queue and receipts.

Use `visual-output-design` to route structural maps to Figma/FigJam when editability matters and charts to quantitative series only. The diagram belongs inside the mechanism/value-chain section, not in a separate visual appendix by default.
