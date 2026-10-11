# Presentation OS — Decision-Grade and Art-Directed Quality Standard (draft)

## Benchmark principle
Benchmark **transferable craft**, not vendor logos or proprietary slide templates. The relevant bar is: decision-quality thinking, supported evidence, compelling storyline, distinctive art direction, readable exhibits, precise execution and reliable handoff. Never claim affiliation with or equivalence to McKinsey, BCG or Deloitte solely because slides appear similar. Translate “wow” into evidence a reviewer can inspect: a memorable supported thesis, purposeful visual rhythm, one signature moment, message-fit layouts, lucid exhibits and an unmistakable audience action.

## Creative direction
Each full deck needs a compact, specific creative brief before authoring. See `creative-direction.md` for the `CreativeDirection` contract, tool-selection matrix and art-direction rules. At minimum, authors must decide the creative thesis, audience response, design system, visual arc, signature moment, slide-by-slide visual grammar, purposeful motion/static choice and primary creation tool. “Use modern design” or “make it dynamic” is not a design brief.

Use the chosen tool well instead of chaining every available tool. Figma Slides generation can produce up to three editable concepts but needs a self-contained prompt, full outline, visual system and explicit slide roles because it has no retained chat context. Canva brief generation and Canva brand-template creation are different routes; a brand kit/template is not applied by its brief-only create path, editing transactions need preview plus explicit approval, and export must be checked separately. Google Slides provides native creation/edit/inspection actions suitable for collaboration and controlled construction but does not supply art direction by itself. In all paths, inspect the actual deck and refine it. Choose a deterministic/native chart renderer for data; use image/video generation only for a clearly useful illustrative beat. Confirm callable actions before planning around any provider.

## Context-specific profiles
| Job | Reader/audience needs | Default story | Visual/word density | Proof of outcome |
| --- | --- | --- | --- | --- |
| Board/investment approval | decide amid competing uses of capital | recommendation → why → alternatives → risks → ask | dense but legible; sources and appendix | named approval decision, trade-off and next action |
| Technology strategy/architecture | understand dependencies and choices | problem → architecture reality → options → transition/decision | accurate mechanisms, diagrams, states and interfaces | credible choices, constraints and responsibilities |
| Transformation execution | prioritize and mobilize | urgency → diagnosis → target → workstreams → risks → ask | roadmap, dependency/owner matrices and governance | prioritization/funding/ownership decision |
| Commercial pitch | believe relevance and act | buyer pain → distinctive insight → proof → offer → action | visual, customer-language, concise | specific commercial next step |
| Live keynote | engage and remember | tension → reveal → demo/proof → memorable close | sparse/large visuals; motion with purpose | recalled message and behavior |
| Workshop/teaching | learn and apply | objective → model → demo → practice → synthesis | stepwise and interactive when real controls exist | correct participant application |
| Analytical leave-behind | understand without speaker | answer → supporting arguments → evidence → risk/appendix | denser explanatory copy, numbered sources | standalone comprehension |

## Authoring craft
- Start with the purpose and audience, not a fixed number of slides.
- On analytical slides, a meaningful `action title` states the supported takeaway. A headline can be weakened/provisional if evidence is insufficient.
- Title-only horizontal read-through should reconstruct the reasoning. Vertical logic: each slide's exhibit directly supports its title, annotation and implication.
- Use design-system grid, restrained color, typographic scale, consistent source-footers, purposeful emphasis, readable contrasts, accessibility and captioning. Avoid decorative chartjunk, 3D and meaningless icon grids.
- Information density must match delivery mode: a standalone executive report can be denser than a stage presentation; over-minimizing analytic evidence is also a defect.
- Align chart grammar with comparison structure: time needs true time; no invented trend from two observations; bar rankings for size; matrix for trade-off; waterfall only for reconciled bridges.
- Motion/video only when it explains sequence, system or emotion better than a static view; include a static fallback and format-specific validation.
- Establish a visual arc (orient → tension/contrast → proof → implication/reveal → resolution/ask, adapted to the actual communication job), and vary slide grammar when the message changes. Keep adjacent slides from repeating the same template without a reason. Reserve the strongest scale/contrast or image moment for the most consequential supported insight.
- Make the deck subject-specific: a deliberate visual thesis, useful metaphor where appropriate, tailored examples/imagery and a clear opening promise. Avoid generic blue-gradient consulting wallpaper, filler agenda pages, arbitrary matrices, stock icon grids and decorative card layouts.
- Give every slide one dominant idea and focal point. The title advances the argument; the exhibit proves or clarifies it; short annotations explain why it matters. “Dynamic” is purposeful change in focus, visual energy, or reveal—not gratuitous transitions.
- Design the ending for action or recall: a concrete next decision/step and owner/timing when supported, or a memorable conclusion. Never fabricate a commitment to strengthen a pitch.
- Keep analytical leave-behinds self-explanatory and live presentations readable at distance. Do not create false minimalism by hiding caveats, sources or decision logic.
- Illustrative generated images are not suitable to encode actual numeric series, product performance, real people or client org truth.

## Distinct strategy vs communication quality

Strategy OS owns option substance, economic/organizational feasibility, independent challenge and approval of strategic recommendations (STR-06/07/09/10; STR-17 evaluates this). Presentation OS owns truthful **communication** of those findings, audience narrative, design, slides and artifact/export quality (PRES-01 evaluates this). Keep their review states separate: a polished deck cannot pass an unrun strategy review, and an excellent strategy may still be communicated badly. Do not require Strategy OS for keynotes, training or local slide editing unless the user's actual intent requires new strategic choices.

STR-12–STR-15 supply domain-specific semantic models and report/exhibit profiles for PESTEL, Porter, SWOT/TOWS and competition/strategy outputs. They must not become a second Canva/Figma deck engine. The shared `visual-output-design` renders individual exhibits; `report-composer` assembles chat-native reports; Presentation OS builds explicit decks when requested.

## Two-layer review checklist
**Partner/editorial:** communication question answered, audience ask, fidelity to source domain findings/options, unsupported claims escalated to source owner, numerical provenance, audience objections, transitions and detail. The domain's strategic-option challenge and substantive thesis validation are independent from this presentation review.
**Art director/production:** montage coherence; each slide readable in context; overflow/clipping; tables/charts labels; hierarchy; alignment/grid; contrast; density; typography and fonts; consistent source lines; native object editability; asset license; animation/export parity.

**Art direction gate (reviewed independently of factual integrity):** specific creative thesis; first slide earns attention and states a promise; at least one memorable, evidence-backed signature moment; pacing has intentional contrast; layouts change with the communication job; visuals look made for this subject rather than interchangeable with a generic template; final slide lands the intended action or recall. Any missing item should be repaired or disclosed as `MAJOR` when it materially weakens the requested persuasive impact. A style makeover cannot compensate for a weak or unsupported argument.

Classify issues `CRITICAL` (fabricated/misleading/secret/major blocking output), `MAJOR` (unsupported decisive claim, broken story, unreadable exhibit, wrong artifact), `MINOR` (cosmetic or local polish). A single critical/major open defect blocks release; **do not average defects into a pass**. Independent blind review is recommended for benchmarking, not assumed.

## Observable success
- Reviewer can infer the argument from headlines in order.
- Every decision-relevant value maps to a source/calculation with unit, scope, period and denominator.
- Reader can identify recommended decision/action and what would change it.
- Actual rendered slides are inspected (montage + risk-targeted individual slides); identified issues are corrected with before/after receipts.
- The inspected deck exhibits its stated creative thesis, visual arc, opening, signature moment and close; variation is purposeful rather than a repeated template or random novelty.
- The selected tool was chosen from callable capabilities and used for its comparative strength; no decorative media or extra generators were added without a communication purpose.
- Editability and export parity checks reflect observed artifacts, not vendor promotional claims.
- Benchmark against generic Canva/Figma prompt and no-skill baseline on at least three materially different briefs; compare decision support, argument, evidence, distinctive art direction, slide craft and delivery reliability. Blind adjudication where feasible; all failures documented.

## Selected foundations / vendor limits (checked 2026-10-09)
- Research background for assertion-evidence slides: https://pmc.ncbi.nlm.nih.gov/articles/PMC13432626/
- Figma Slides PPTX/PDF export with editable/flattened selection and restrictions: https://help.figma.com/hc/en-us/articles/24848334599447-Export-from-Figma-Slides
- Canva PPTX download and layout/animation/video caveats: https://www.canva.com/help/download-file-types/
- Canva ChatGPT app behavior/connection: https://www.canva.com/help/connect-chatgpt-to-canva/
- User-facing design may be inspired by general consulting craft, but no unauthorized copying of specific layouts or logos.
