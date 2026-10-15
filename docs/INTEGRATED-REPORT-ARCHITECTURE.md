# Integrated Decision Report Architecture

## Goal
Produce one coherent decision report in which narrative, evidence, visuals, interactive controls and sources are composed
together according to reading flow.

This replaces the weaker pattern of:
- full text answer;
- plus a parallel dashboard/HTML artifact containing the same content again.

## Architecture

Evidence / canonical state
-> Domain skills
-> Workflow synthesis
-> **Report Composer**
   -> ordered sections
   -> narrative/evidence/decision blocks
   -> inline visual slots
-> **Visual Output Design**
   -> renderer selection per slot
-> Chat-native report by default; external artifact only on explicit user request

`report-composer` owns document structure and placement.
`visual-output-design` is the specialized exhibit selector and renderer for all report/presentation media: it chooses suitable chart, diagram, illustration, motion or interactive component tools and returns a source-linked exhibit. Report Composer owns narrative structure; format owners embed the same exhibit semantics into Chat, a website, DOCX, PDF or PPTX. In normal Chat, Cloud Next chart MCP Apps are its inline interactive renderer primitives—not a separate user-facing tool or dashboard.

## Semantic report model
A report contains:
- title;
- decision headline;
- target;
- sections;
- receipts;
- limitations.

A section contains:
- narrative;
- evidence;
- zero or more visual slots;
- interpretation;
- decision/next step;
- provenance;
- uncertainty.

## Targets

### Chat-native report
Use when the runtime can render suitable charts/widgets inline.
The narrative remains in chat and visuals appear in the same conversation flow beside the relevant report section. Cloud Next chart tools request inline display and provide selectable marks/series controls. ChatGPT places an app in its inline app slot; the host does not guarantee arbitrary insertion in the middle of a prose message, so keep related interpretation adjacent in the report text. When converting to DOCX/PDF/PPTX, the owning authoring workflow embeds an appropriate native or static version and records any interaction/editability loss.

### External artifact
Use only when the user explicitly requests HTML, PDF, Figma, a deck, a downloadable file or another external format.
The external artifact may then be the primary report for that request, but this is never the automatic fallback for missing chat-native rendering.

### Chat-native fallback
Use native widgets/charts when available, otherwise tables or structured prose. Preserve section structure and decision logic inside the chat response.

## Interaction
Interactive controls must answer a real decision question.
Examples:
- security price chart: 3M / 6M / 12M;
- valuation: bear/base/bull toggle;
- portfolio: nominal vs look-through exposure;
- OAF: current vs target model toggle.

Do not add filters/tabs solely because HTML supports them.

## Cross-domain adoption
Investment OS, OAF, Commerce, and presentation-of-results workflows should call Report Composer after analytical synthesis. This includes an interactive chart embedded in a chat report; it does not convert a request for a native slide deck into a chat report. Their default delivery target is the chat response.
Visual Output Design remains a shared renderer utility.
New skills/workflows should specify report/visual affordances during specification and authoring.

## Integrity
- presentation cannot introduce facts;
- visuals inherit workflow evidence standards;
- canonical receipts remain explicit;
- unknown relationships remain unknown;
- external artifacts are derivative and noncanonical unless a separate storage contract says otherwise;
- absence of a preferred embedded renderer never authorizes unsolicited HTML/PDF/Figma/deck generation.
