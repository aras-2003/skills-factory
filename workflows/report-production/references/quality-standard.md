# Report OS — Analytical and Document Quality Gates (draft)

## Professional quality is multidimensional

**Analytical integrity:** claims adequately sourced; assumptions distinguished from observations; methods and comparators sound; conflicting evidence visible; choices and approval statuses unchanged from source domain; uncertainty proportional to support. Domain correctness belongs to the source specialist.

**Information architecture:** compelling but accurate executive summary; purpose-led chapters; scope/method/findings/conclusions in a reader-useful order; differentiated hypotheses and findings; consistent terms; appendix for detailed substantiation rather than padding.

**Document craft:** readable typographic hierarchy, logical margins, accessible contrast, correct numbering/TOC, source footnotes or endnotes when supported, stable captions/crossrefs, legible data tables, real chart labels/units/sources, proper page breaks, avoid widows/orphans and cut-off images. Page format must match reading mode and device; PDF is not a dump of slides.

**Delivery integrity:** actual DOCX or Google Doc where requested; export to actual PDF where requested; programmatic/render-based page verification and content/format fidelity. Check table splits, line wrapping, crossref/TOC target, hyperlinks, font replacement and images. Editability is evaluated from produced file behavior, not its extension. No PASS from a specification or intended pipeline.

## Profiles (select, never force)
- Board/decision report: decision, context, alternatives, evidence, trade-offs, risk, decision rights, implementation and annexes.
- Deep strategy/market study: executive findings, method/definitions, environment/industry/competition, choices/implications, uncertainty, scenario/limitations, appendices.
- Technical/architecture study: decision context, as-is/constraints, architecture options, dependencies, trade-offs, risk, migration, validation, diagrams/ADRs.
- Due diligence: scope, diligence method, verification matrix, findings and severity, alternative explanations, unresolved items, remedies.
- Research/white paper: question, method, critical sources, synthesised results, limitations, implications and references.

If a decision only needs a 2-page memo, do not create a 35-page report. If sources demand real depth, do not compress materially needed evidence merely to look polished.

## Review and stop
- Content reviewer checks reasoning, references, consistency and fidelity to domain results.
- Document reviewer inspects actual **all rendered pages**, plus a montage for consistency and close-up of high-risk pages.
- A `CRITICAL` fabricated claim/privacy leak/missing requested file blocks release. A `MAJOR` broken table, missing necessary evidence, invalid TOC/page refs or unreadable section requires fix or `REVIEW_REQUIRED`. Cosmetics `MINOR` are prioritized separately; never average into a green score.
- Repairs target responsible section/provider; re-render and compare changed pages and document index/navigation.
- Compare candidate report with generic no-skill baseline and specialist-produced brief/report in at least 3 distinct profiles; distinguish source quality from layout quality, retain independent observer receipts.
- Do not claim consultant-branded affiliation or proprietary template equivalence.
