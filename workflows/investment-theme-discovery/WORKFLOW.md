# Investment Theme Discovery Workflow

## Purpose
Research a structural or cyclical trend, map where economics accrue and create an XTB-focused research queue without equating narrative strength with investability.

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
9. Persist a new theme version, sources and candidate opportunities through investment-record-store.
10. Underwrite only the few candidates where theme economics and security setup justify deeper work.

## Decision rules
- demand growth can coexist with bad supplier economics;
- second-order beneficiary claims require evidence of value capture;
- thematic-provider output is discovery evidence, not canonical state;
- theme discovery never issues position sizes.

## Output contract
Theme mechanism | changes since prior view | indicators | value chain | beneficiaries/losers | crowded assumptions | invalidation | XTB research queue | provenance | persistence receipt.

## Stop conditions
Stop once a falsifiable theme map and bounded research queue exist.

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
