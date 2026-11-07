# Investment Security Review Workflow

## Purpose
Evaluate one XTB security from thesis creation through falsification, valuation, portfolio fit and a policy-consistent lifecycle/sizing state.

## Entry criteria
Enter for one explicitly identified security needing integrated underwriting, valuation and challenge; do not choose it for mere ticker news, watchlist preview or broad theme mapping.
The default is **analysis only**. A user request to research, analyze, review, screen, size or evaluate does NOT authorize writing to any canonical store. Missing canonical read is BLOCKED_CANONICAL_READ, not a fabricated empty history.

## Context mode

Use `CANONICAL` by default. Attempt the required `investment-record-store` read and stop with `BLOCKED_CANONICAL_READ` if the capability or read is unavailable. Never infer empty history, portfolio or policy state, and never switch modes silently.

Use `USER_SUPPLIED_CONTEXT` only when the user explicitly requests that mode and supplies the context they want considered in the current request or attached material. Identify the mode in the report, distinguish user-supplied statements from independently verified facts, and do not claim a canonical read or a complete account history. A supplied thesis can be challenged only as that supplied baseline; if it is absent, return `INSUFFICIENT EVIDENCE` for thesis challenge. Missing portfolio or policy context blocks portfolio fit and sizing. This mode is analysis-only and never attempts a canonical write.

## Required skills
- security-underwriting
- valuation-scenario-review
- thesis-challenge
- investment-record-store in `CANONICAL` mode only

## Optional skills
- trend-theme-research
- portfolio-state-review
- position-sizing-review
- decision-journal-update

## Sequence
1. Resolve context mode. In `CANONICAL`, read prior research, thesis history, current portfolio and policy through investment-record-store; emit its actual canonical READ receipt. In `USER_SUPPLIED_CONTEXT`, use only explicitly supplied context and record each missing section; do not invoke or imply investment-record-store.
2. Use structured equity/ETF research plugins for context and consensus framing, then underwrite the security with an explicit horizon.
3. Require explicit WHY THIS / WHY NOW and build historical context before current-state conclusions:
   - 5Y price history when available plus 1Y setup;
   - 12-20 quarter key KPI history;
   - valuation history where reliable;
   - dated material events aligned to major price/KPI moves;
   - observed move vs likely cause with confidence.
4. Verify decision-critical metrics in primary-source context; use Firecrawl to retrieve/parse filings or IR pages when useful.
5. Run the value-trap gate and Financial Quality Audit (#318): reconcile CFO, capex, working capital, leases, advances, dilution, normalized FCF, leverage, maturities, coverage and cycle risks where applicable, across three to five fiscal years and comparable current/prior YTD. Show PASS/WARN/BLOCK, per-value sources, reasons and invalidation triggers. Mark missing/conflicted facts unresolved; bank, insurer and ETF data need their own accounting path.
6. Run the hard evidence-sanity gate: period, units, GAAP/non-GAAP, quarterly/annual, per-share/absolute, arithmetic and scale.
7. If any critical metric remains UNVERIFIED/CONFLICTED, classify VERIFY/RESEARCH; block numeric valuation and sizing; persist the gap if possible and return.
8. Only after both gates pass, build the bear/base/bull Valuation & Opportunity Card with an industry-fit method, price/currency, fair-value range, separately calculated margin of safety and upside, horizons, provenance and sensitivity. A BLOCK gate forbids an attractive rating and FCF-based valuation.
9. For Tactical Review peer comparison (#306), use only peers with matching sector, industry, business model, as-of, definitions, periods, bases, units, currency and forecast horizon. Show exclusions and N/M reasons; require three peers for a compact table and five for descriptive percentiles. Forward P/E / EPS CAGR PEG is descriptive only; PEG=1 is not a buy signal. Any optional plot must consume the same table snapshot and preserve source/date/filter provenance.
10. Separate business-thesis strength, security attractiveness, valuation, catalyst/timing, portfolio fit and confidence. Include five-stage business lifecycle using the deterministic security-underwriting classifier only after verification; label affinity scores uncalibrated and surface missing metrics. Never interpret lifecycle as valuation or trade recommendation.
11. Run thesis-challenge independently. Return up to three materially plausible countercases ranked by evidence and impact; trace sources through operating and valuation consequences. Missing evidence remains unresolved, not a fabricated bear case.
12. Classify research state: REJECT / WATCH / RESEARCHED / THESIS SURVIVES / THESIS WEAKENED / INVALIDATED.
13. If portfolio action is considered, parse policy semantics literally and run portfolio-state-review/position-sizing-review as needed.
14. Determine persistence scope **after** analysis. Without explicit per-action approval or a verified standing write mandate for the exact canonical target and operation, do not write; return NOT_WRITTEN (including read-only, preview-only, unspecified, or unknown permissions).
15. When and only when separately authorized, append research events/sources/signals via investment-record-store. A **new thesis version**, thesis activation or an owner lifecycle decision requires its own explicitly approved operation. Do not overwrite prior thesis history or reuse past test/production authorization.
16. If an independently approved lifecycle decision was made, append only the decision-journal event within that approved scope.
17. Report SAVED only with a real successful canonical WRITE receipt including target/time/id; otherwise WRITE_FAILED or NOT_WRITTEN. Research plugins, Data analytics and local files never count as canonical persistence.

## Decision rules
- company quality, security attractiveness and portfolio fit are different questions;
- structured research speeds discovery but does not replace primary verification;
- extreme figures must be verified, not rejected by magnitude;
- source URL present != extracted figure verified;
- unverified critical metrics block valuation and numeric sizing;
- a BLOCK cash-flow quality gate blocks attractive ratings and FCF-based valuation;
- margin of safety and upside are separate metrics with separate formulas;
- review threshold != hard ceiling.

## Related components and scope
- This workflow provides the single-security evidence package consumed by Tactical Review (#306); keep the detailed valuation card here rather than expanding the daily risk brief.
- Reuse Financial Quality Audit (#318) for multi-year cash-flow and return evidence and the existing bear-case review (#307) for independent downside challenge; do not duplicate or override either result.
- Pass explicitly separated quality, valuation, catalyst/timing, portfolio-fit and confidence inputs to the horizon-aware opportunity score (#360). This workflow does not replace that ranking, portfolio review or an owner decision.
- Keep the sequence analysis-only. A valuation card or cash-flow gate never authorizes a canonical write, portfolio action or trade.

## Output contract
Context mode and coverage | WHY THIS / WHY NOW | historical price/KPI/valuation context | material event timeline | observed moves vs likely causes + confidence | business thesis | value-trap gates and reasons | evidence-sanity status | verified/blocked metrics | Valuation & Opportunity Card or NOT_SCORED | priced-in expectations | separate quality/valuation/catalyst/portfolio fit/confidence | strongest countercase | thesis state | portfolio constraints | lifecycle/sizing state if permitted | exact evidence gaps | next trigger | canonical READ/WRITE receipts only when actually produced.

## Stop conditions
Stop before sizing if policy/portfolio context is missing.
In `CANONICAL`, stop at a missing or failed required store read. In `USER_SUPPLIED_CONTEXT`, continue only within the supplied evidence boundary; do not infer unavailable history, portfolio state or policy.
Stop valuation and numeric sizing if critical evidence is unresolved.
Do not write when the user requested advice only or canonical identity/authorization is unverified. A failed or inaccessible canonical read must not be treated as a verified empty store; explain the missing baseline and limit analysis.

## Integrated report presentation
Render the report directly in the chat response by default. External HTML/PDF/Figma/deck/file output is allowed only when the user explicitly requests that artifact or format.

After analytical synthesis, call `report-composer`. Use `visual-output-design` to render only the local visual slots.

Default profile:
- investment view / thesis state;
- WHY THIS / WHY NOW;
- business performance with KPI strip and **required inline five-stage Business Lifecycle visualization**, generated from the classifier's actual output; show a highlighted phase, five affinity bars, uncalibrated-score warning and revenue/margin evidence. If data are insufficient, render the same five-stage panel as NOT CLASSIFIED with N/A scores. Use a documented renderer or show explicit BLOCKED_NO_RENDERER plus five-stage text fallback;
- a required inline 5Y price-history visual plus 1Y current-setup view when verified time-series data exist; use the best concrete renderer.
- a required KPI-history visual for key decision-driving metrics when historical data exist;
- dated material-event timeline tied to major price/KPI changes;
- fundamental change;
- valuation / priced-in expectations with scenario range when permitted;
- catalysts and risks;
- portfolio fit / sizing constraints;
- decision state / next trigger;
- evidence and canonical receipts.

Historical charts belong inside the sections they explain, not in a separate dashboard. Default KPI history is 12-20 quarters. Use a documented, callable interactive renderer only when this runtime exposes one; otherwise use the static chart renderer and label the returned image static.

**Renderer and interaction rule:** render each supported required price/KPI visual with an actual deterministic renderer. Use an interactive component only when the current runtime documents and exposes a callable interface. Otherwise embed the static renderer's returned image inline and label it static. If the user requested selectors or filters that are unavailable, mark the control feature BLOCKED_NO_RENDERER while retaining a successfully rendered static visual. If the visual itself cannot be rendered, mark that slot BLOCKED_NO_RENDERER or FAIL_RENDERER_INVOCATION; do not simulate a widget call.

If evidence-sanity blocks valuation, show the blocked state rather than a fabricated range.
Do not collapse business quality, current-price attractiveness and portfolio fit into one score.
