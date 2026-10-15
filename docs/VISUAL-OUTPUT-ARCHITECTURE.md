# Visual Output Architecture

## Goal
Render professional evidence-backed visual components without coupling domain analysis to one rendering tool.

This is the shared exhibit selection and rendering layer used by chat reports, long-form reports, slide decks and explicitly requested interactive HTML reports. It is component-level; it does not own a full report or deck.

## Layers
1. Evidence and canonical data.
2. Domain analysis in existing skills/workflows.
3. Composition owner: `report-composer` for chat; `report-document-architecture` and `report-document-authoring` for DOCX/PDF; `presentation-exhibit-design` and `presentation-slide-authoring` for PPTX/decks; the existing Interactive Experience workflow for full interactive HTML/site reports.
4. Semantic `ExhibitSpec` for each local slot: comprehension job, claim/evidence IDs, data, units, provenance, intended medium, interactivity, accessibility and editability requirements.
5. `visual-output-design` selects a modality-specific renderer and creates/verifies that component.
6. A target adapter embeds the component in the requested final material: chat MCP App, web HTML/CSS/JS, editable DOCX/PPTX object where supported, or static/vector PDF element. Interactions are preserved only when that target supports them; otherwise state the loss and use the best faithful static fallback.

The rendered visual is derivative presentation, not a new system of record.

## Responsibility boundary
- `report-composer` owns reading flow, section order, progressive disclosure and visual placement.
- `visual-output-design` is the shared specialist that chooses and renders charts, diagrams, tables, illustrative imagery and local interactive components. It dispatches to existing specialized media/diagram/deck capabilities where appropriate; it must not reproduce those specialist workflows. The same semantic ExhibitSpec travels across target formats, but each final artifact is produced and reviewed by its own format owner. OpenAI MCP Apps defines the in-chat UI bridge and display modes; the optional Apps SDK UI library supplies ChatGPT-styled React components, not data visualization semantics. For richer interactive charts, a declarative grammar such as [Vega-Lite](https://vega.github.io/vega-lite/docs/) is a candidate renderer after checking bundle size, CSP and target-host compatibility.

Do not use `visual-output-design` to create a second full dashboard beside an already complete report unless explicitly requested.

## Renderer routing
- **Quantitative charts:** deterministic chart renderer, preserving exact values, labels, units and source data. The Cloud Next MCP Apps renderer is the default inline interactive implementation in normal Chat; it provides selectable marks and line-series toggles. A more expressive grammar such as Vega-Lite is a future renderer option when actual chart needs exceed the existing capability, not a second report layer.
- **Diagrams:** semantic, editable diagram formats or a deterministic SVG/diagram renderer. Use Mermaid where its supported grammar and host rendering meet the need; never imply interactions the host/security mode disables.
- **Illustrations and motion:** generated image/video assets when they improve comprehension and the content is not factual measurement. GIF is an output encoding, not a universal presentation component; choose still image, short animation or video based on the audience/device and requested artifact.
- **Chat UI shell:** MCP Apps is the cross-host UI delivery contract. ChatGPT's `@openai/apps-sdk-ui` may provide accessible visual primitives for a richer React component; it is optional, ChatGPT-specific UI polish and not a chart/diagram-generation engine. Keep the MCP Apps standard as the portability layer.
- **Tables and structured chat:** use for evidence ledgers, precise values and fallbacks when a visual adds little or no suitable renderer is available.
- **DOCX/PDF/PPTX embedding:** defer to the native document/deck authoring capability. Prefer editable native charts/shapes when actually supported; PDFs commonly flatten interactions, so provide a static accessible figure and preserve the source data/ExhibitSpec alongside the file when needed.
- **Figma / slide authoring:** delegate to those specialist workflows only when an editable design or actual deck is the requested deliverable.
- **Interactive HTML report:** create as a full external report only when explicitly requested. A single inline chart/diagram widget remains a local exhibit in the chat report and does not become an HTML-report task.

No single renderer should generate every modality or own every output format. `visual-output-design` routes a shared semantic exhibit contract to specialized renderers; target-format owners embed it in the final report, website or deck and report capability, execution, editability and display states separately.

Runtime receipts and client display evidence have different owners: the model/tool receipt establishes payload generation, while the external evaluator establishes whether the target client actually displayed it. Record evaluator UI evidence separately (for example, a timestamped screenshot or DOM observation); never ask the model to infer that observation or treat its `NOT_OBSERVABLE` status as proof that display failed.

## Domain patterns
Investment OS: normalized performance, allocation/concentration, overlap, valuation ranges, catalyst/risk timelines and opportunity cards.

OAF: domain heatmaps, causal maps, operating-model maps, governance flows, capability views and transformation roadmaps.

Commerce: unit-economics bridges, competitor matrices, evidence heatmaps, acquisition funnels and shortlist cards.

Career: mandate/authority matrices, role comparisons, recruitment timelines and evidence-gap views.

## Boundaries
- Visualisation cannot introduce new facts.
- Missing data stay missing.
- Canonical read/write receipts remain auditable text.
- External visual artifacts are not canonical state.
- Factual visuals retain source and as-of context.
- In ChatGPT, inline MCP Apps appear in the conversation's app slot (before the generated prose), not at an arbitrary cursor inside a message. Keep interpretation adjacent and do not claim arbitrary in-message insertion.
- If chat cannot truly embed a visual inline, the system must use the best chat-native fallback.
- Do not create HTML/PDF/Figma/deck/file output as an automatic fallback; external artifacts require explicit user intent.

## Target-format embedding contract

| Target | Embedding default | Interaction policy | Owner / QA |
| --- | --- | --- | --- |
| Chat | Inline MCP App or native chat element alongside narrative | Preserve only documented controls; verify host display independently | Report Composer + client observation |
| Web / interactive HTML | HTML/CSS/JS component in the report page | Enable tested controls and responsive/mobile behavior | Interactive Experience / Site workflow + browser QA |
| DOCX | Editable native chart/diagram when supported; otherwise accessible image with caption and data provenance | Keep controls only if authoring/runtime supports them; disclose flattening | Report Document Authoring + reopen/render review |
| PDF | Vector or high-resolution static figure with caption, source and accessible text where supported | Treat as static unless a real PDF control has been tested | PDF export + page-level review |
| PPTX | Editable chart/shapes where supported; otherwise placed image with alt text/source | Preserve animation/interactivity only when actually supported and verified | Presentation Slide Authoring + exported deck QA |

For combined output requests, render from the same source-backed ExhibitSpec but perform output-specific layout and validation separately. A PASS in one format does not certify another.
