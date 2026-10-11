# Investment Opportunity Hunter Workflow

## Purpose
Actively discover new investment opportunities globally, with XTB availability strongly preferred for actionable ideas, and reduce them to a small evidence-backed shortlist. Discovery must explain why each promoted name is interesting **now**, using measurable changes, historical context and primary evidence rather than cheapness or familiarity.

## Entry modes
- broad scan: scan globally, then verify XTB availability before calling an idea actionable;
- watchlist change scan: detect names that became materially more or less interesting;
- theme-led scan: start from a validated theme and find candidate beneficiaries.

## Required skills
- market-opportunity-scan
- investment-record-store

## Optional skills
- investment-attention-triage
- trend-theme-research
- portfolio-state-review
- security-underwriting
- valuation-scenario-review
- thesis-challenge

## Sequence
1. Read current policy, portfolio, watchlist, prior opportunities and signal history through investment-record-store. Emit the canonical READ receipt.
2. If canonical history is unavailable, continue only as a fresh screen and state that no prior-state comparison was possible.
3. Use installed structured equity/ETF research plugins and current external research for broad discovery. Do not seed the scan primarily from existing opportunities/watchlist.
4. Run market-opportunity-scan and create a broad radar of roughly 10-15 names.
5. Reject/defer candidates that lack:
   - WHY THIS;
   - WHY NOW;
   - at least 2-3 measurable decision-relevant signals;
   - a clear failure case.
   Cheapness, a low multiple or a drawdown alone cannot pass this gate.
6. Verify decision-relevant claims with primary sources; use Firecrawl for live retrieval/parsing when useful.
7. Keep fundamental, valuation and market/trend evidence in separate fields and attach dated provenance/confidence.
8. For promoted names, build historical evidence:
   - 5Y price context when available;
   - 1Y current setup;
   - 12-20 quarter key KPI history;
   - valuation history where reliable;
   - dated events aligned to material price/KPI changes.
9. Separate observed historical moves from likely causes. Causal interpretation must cite supporting events/data and carry HIGH/MEDIUM/LOW confidence or UNKNOWN.
10. Use investment-attention-triage when materiality is unclear.
11. If a theme drives the setup, use trend-theme-research before attributing benefit to a company.
12. Rank the radar by evidence quality, asymmetry, material change and portfolio distinctiveness. Promote only the best 2-3 to detailed analysis by default, and say exactly why they outranked alternatives.
13. For those 2-3, run security-underwriting and valuation-scenario-review.
14. Run thesis-challenge before promoting a candidate to a conviction queue.
15. Confirm XTB availability before calling an idea actionable.
16. Persist research state through investment-record-store only, within this allowlist:
   - sources and evidence links that support material verified claims;
   - research events/signals only for material new or changed evidence;
   - promoted candidates as canonical opportunities with research status RESEARCH_CANDIDATE, WATCH, DEFER or REJECT.
   A direct user request to run discovery, scan or produce a report is **not by itself** write authorization. Require an explicit user instruction to save research state or a previously documented, verifiable standing mandate covering this exact workflow, record type and canonical target. Read-only, preview, test, no-save, or unknown boundaries are always non-writing. Do not persist the generated report itself as canonical state.
17. Before writing, pass the evidence gates, deduplicate by stable instrument identity against current/prior opportunities, and write only new or materially changed research state. Update disposition/history instead of creating a duplicate. Do not write speculative candidates that remain in raw discovery.
18. Emit a canonical WRITE receipt listing each entity class written, skipped or failed. Data/analytics outputs and local files are NONCANONICAL.
19. Do not size or label BUY/SELL here; route portfolio action to investment-security-review or position-sizing-review.
20. Owner-decision writes (BUY/SELL/REDUCE/EXIT, policy changes, thesis activation, transaction execution) remain separate and require the appropriate explicit authority.

## Evidence gates
- no shortlist promotion without WHY THIS / WHY NOW and measurable evidence;
- cheapness/drawdown alone fails the gate;
- current claims require as-of/source dates;
- structured research is discovery evidence, not canonical state;
- critical figures require primary-source sanity checks;
- XTB availability must be confirmed before a candidate is called actionable;
- a promoted research candidate may still be persisted as `RESEARCH_CANDIDATE` while XTB status remains unverified;
- a report/discovery request alone is not write authorization; without an explicit or verified standing mandate, return `NOT_WRITTEN` and do not persist canonical research state;
- social/news attention alone cannot pass discovery.

## Output contract
### Broad radar
10-15 names by default:
Ticker | WHY THIS | WHY NOW | measurable evidence | valuation/expectations | failure case | portfolio distinctiveness | XTB status | disposition (PROMOTE/WATCH/DEFER/REJECT).

### Detailed shortlist
2-3 names by default:
- explicit reason for selection over alternatives;
- 5Y price history + 1Y current setup when available;
- 12-20 quarter key KPI history;
- valuation history where reliable;
- material event timeline;
- observed moves vs likely causes + confidence;
- thesis/setup, catalyst, strongest countercase and next evidence gate;
- canonical persistence status `NOT_WRITTEN`, `SAVED`, or `WRITE_FAILED`, with actual receipts only for attempted writes; identify which promoted candidates were written or updated when authorized.

## Stop conditions
Stop broad discovery when roughly 10-15 credible research candidates remain.
Stop detailed work after the best 2-3 have passed the evidence gate unless the user asks for a wider deep dive.
Stop deeper work when the evidence gap is larger than the apparent opportunity.

## Integrated report presentation
Render the report directly in the chat response by default. External HTML/PDF/Figma/deck/file output is allowed only when the user explicitly requests that artifact or format.

After analytical synthesis, call `report-composer` to produce one integrated opportunity report. Use `visual-output-design` only for the inline visual slots selected by the composer.

Default profile:
- discovery context and search logic;
- broad radar (10-15 candidates) with explicit promote/watch/defer/reject rationale;
- top 2-3 candidate-by-candidate sections;
- a required inline price-history visual for each detailed candidate when verified time-series data are available; use the best concrete renderer in the current runtime.
- key KPI history visual(s) for each detailed candidate where material data exist;
- dated material-event timeline and causal interpretation;
- cross-candidate comparison;
- research queue / next actions;
- canonical receipts and limitations.

For each detailed candidate, the default price horizon is 5Y plus a 1Y current-setup view when data are available. KPI history defaults to 12-20 quarters. Use a documented, callable interactive renderer only when the current runtime actually exposes one; otherwise use the static chart renderer and label the image static.

**Renderer and interaction rule:** invoke an actual deterministic chart renderer for every supported chartable slot. Use a native interactive component only when this runtime documents and exposes a callable interface. Otherwise embed the static renderer's returned image inline and label it static. If the user requested selectors or filters that are unavailable, mark that control feature BLOCKED_NO_RENDERER while retaining any successfully rendered static chart. If the visual itself cannot be rendered, mark that exact slot BLOCKED_NO_RENDERER or FAIL_RENDERER_INVOCATION. A tool attempt, capability mention, URL, chart JSON or base64 string is not an included visual.

**Output audit:** before returning, reconcile every required slot for every detailed candidate against the actual inline visuals in the report. One successful chart does not cover another candidate's missing chart. Never expose data:image/...;base64,..., raw base64 or serialized media in user-facing text.

Use a compact in-chat shortlist dashboard after the executive summary/radar to compare candidate, status, why-now evidence, valuation/expectation risk, portfolio fit and next gate. It is a readable table/card group inside the report, not a claim of an interactive dashboard and not a separate file. Keep historical charts adjacent to each candidate's analysis.

When at least two verified price series overlap on comparable dates and use compatible adjustment bases, prefer one shared price line indexed to 100 at the first common date. Keep candidate KPI visuals separate and retain original units. Use lines only for three or more dated observations; show two points as a period comparison, not a trend. State normalization, FX/dividend treatment, source and as-of date.
