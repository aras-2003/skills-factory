# Investing Domain Audit — Iteration 07

**Date:** 2026-11-06
**Scope:** GitHub issues #231, #306, #307, #318. Coordination umbrella #322 is tracking-only.
**Runtime evidence:** Skills Factory Cloud Next Lab `1.38.464`, release `1.38.464+854117b7128d`, verified source revision `854117b7128dcc88e5c46407b8bee71309af7357`; receipts and observed limitations are in [the runtime evidence record](../../evals/campaigns/iteration-07-investing-quality-2026-11/runtime-evidence.md).
**State:** Source audit plus partial exact-candidate runtime review. Runtime tool calls ran, but the integrated workflow is blocked by a required capability gap; no maturity or release claim.

## Inventory and exact source versions

Versions below are read from repository source metadata at this audit's base revision. Changed versions identify the Iteration 07 candidate. Runtime inventory is a separate snapshot, not evidence that the local candidate is loaded.

| Component | Source version | Cloud Next inventory at pinned revision | Iteration 07 use |
|---|---:|---:|---|
| investment-os-review | 0.3.2 | 0.3.2 | Entry router; multi-position requests stay in portfolio review |
| investment-security-review | 0.4.4 | 0.4.4 | Route selected it; exact workflow load confirms canonical-read gate; execution stopped because the required store tool is absent |
| security-underwriting | 0.5.3 | 0.5.3 | Exact candidate loaded; AMD financial-quality probe in evidence record |
| valuation-scenario-review | 0.3.1 | 0.3.1 | Exact candidate loaded; real-source peer helper probe returns insufficient peers offline |
| thesis-challenge | 0.1.2 | 0.1.2 | Exact candidate loaded; direct two-countercase probe in evidence record |
| investment-record-store | 1.0.2 | 1.0.2 | Canonical reads; writes remain separately authorized |
| investment-portfolio-review | 0.5.1 | 0.5.1 | Multi-holding analysis boundary |
| portfolio-state-review | 0.7.2 | 0.7.2 | Optional portfolio context |
| position-sizing-review | 0.3.1 | not listed in investment-like runtime subset | Optional; missing portfolio/policy blocks sizing |
| investment-attention-review | 0.2.2 | 0.2.2 | Daily risk/attention path, not detailed valuation output |
| investment-portfolio-observation | 0.2.1 | 0.2.1 | Holdings observation path |
| investment-opportunity-hunter | 0.5.1 | 0.5.1 | Candidate discovery; not single-security valuation |
| investment-theme-discovery | 0.2.1 | 0.2.1 | Theme-level route boundary |
| market-opportunity-scan | 0.4.2 | 0.4.2 | Broad scan boundary |
| investment-attention-triage | 0.2.4 | 0.2.4 | Attention queue |
| investment-policy-design | 0.1.0 | 0.1.0 | User policy; no inferred permissions |
| decision-journal-update | 0.1.1 | not listed in investment-like runtime subset | Explicitly approved lifecycle event only |
| historical-decision-replay | 0.1.0 | not listed in investment-like runtime subset | Historical as-of evidence boundary |
| investor-pattern-research | 0.1.1 | 0.1.1 | Behavioral reflection; not an issuer-data source |
| thesis-monitor | 0.3.2 | 0.3.2 | Active-thesis monitoring only |
| technical-structure | 0.1.1 | 0.1.1 | Technical context; not fundamental quality |
| trend-theme-research | 0.1.0 | not listed in investment-like runtime subset | Optional theme context |
| fundamental-intelligence Python package | no SKILL.md/runtime skill identity | no standalone skill entry | Local deterministic helpers only; workflow must not imply runtime invocation |
| financial-quality helper | packaged under security-underwriting `scripts/financial_quality.py` | candidate helper is not in current loaded runtime package | Caller-reviewed deterministic calculations, no source fetching |
| peer comparison and plot helpers | packaged under valuation-scenario-review `scripts/peer_comparison.py` and `scripts/peer_growth_plot.py` | candidate helpers are not in current loaded runtime package | Same-snapshot comparison/plot; no recommendation |

The exact runtime now includes all four candidate versions. Runtime skill loading alone is not behavior evidence: the runtime receipts prove package identity, while semantic outcomes are described separately and their limits retained. The runtime reports no local Python execution capability. The routed integration workflow requires `investment-record-store`; that tool is not in the runtime capability list, so the workflow must stop at `BLOCKED_CANONICAL_READ`. It was not treated as an empty portfolio or history.

Canonical history is read through `investment-record-store`; the single-security workflow forbids treating an inaccessible read as an empty history and keeps writes separately authorized. The required store capability is absent in this exact runtime, so integrated security review is blocked before underwriting. Filing discovery/parsing may use Firecrawl where available, but it is a retrieval aid, not verification. Any missing store read, source retrieval or renderer remains BLOCKED/NOT_OBSERVABLE under the current workflow fallbacks.

## Route and request boundaries

Existing routing fixtures cover an English single-security request, an English security-plus-sizing request, a Polish broad opportunity request, an English theme request, a Polish portfolio-observation request, and a Polish policy-learning request. The source workflow already declares the one-security versus broad-theme/portfolio boundary. This iteration adds supplemental controls for exactly two and exactly twenty candidates and Polish VAT/PIT plus English NASA acronym near-misses. An existing ambiguous-shares case still requires route clarification. This iteration adds behavior cases for valuation peer quality and thesis challenge; it does not claim a new router runtime pass.

Required audit coverage for the release campaign includes:

- English and Polish single-security analysis; distinguish one named issuer from multiple holdings.
- Broad opportunity scan, theme mapping and ticker-news near-misses must not invoke full single-security underwriting by default.
- Tax, VAT/PIT, or unrelated acronyms and ambiguous ticker tokens must not be mistaken for investment intent without context.
- “Top 2”/“top 20” requests must preserve requested cohort size and not be silently rewritten as a full security review.
- Read-only research never authorizes canonical writes; failed reads are not an empty portfolio or thesis history.

## Evidence gates and calculation semantics

- #318: source reviewed facts only; no web retrieval inside the calculation helper. Every reported fact must retain a source URL, publication date, period, unit, currency, and accounting basis. Accept 3–5 contiguous FY periods and require latest/prior same-quarter YTD with period-length and metric-definition comparability. Missing or conflicting critical values block dependent outputs. Unit scale conversion is allowed; FX conversion is not implicit. CFO less capex (with explicit sign convention) defines FCF. FCF conversion only divides by positive net income. ROIC requires sourced NOPAT and average invested capital. Balance-sheet, working-capital, stock-compensation, one-off/recurring and share facts remain per-value traceable; adjusted bases are displayed separately. Banks, insurers, REITs and ETFs return an alternative-path state instead of zero-filled industrial metrics. No write is attempted.
- #306: same sector/industry/business model and as-of date before peer inclusion; compatible definition, period, basis, unit, currency and forecast horizon before metric comparison. Unsupported/stale/future/nonpositive forward evidence is N/M with a reason. Table threshold is 3 peers; percentile threshold is 5. PEG is forward P/E divided by positive EPS CAGR in percentage points; PEG=1 is a descriptive heuristic. No cross-sector rank, cheapness conclusion, recommendation or trade.
- #307: at most three countercases, selected by materiality and evidence; each has dated sources, a causal path and explicit horizon. Missing evidence is unresolved. Business deterioration, valuation, priced-in expectations, timing and sizing remain distinct. No compelled quota or trade advice.
- #231: sources, periods, units, uncertainty, freshness and write authorization remain explicit. No maturity transition is allowed from this audit alone.

## Planned validation and residuals

The Iteration 07 source campaign is a new, hash-bound campaign. It must include focused helper tests and behavior case IDs for #306/#307/#318, plus unchanged routing boundary fixtures as regression controls. Historical October R20/R17/R18 result files remain immutable. Validation order: complete implementation and catalog/package generation first; then focused calculation tests, repository validation, campaign/hash validation, full CI-equivalent checks, and runtime only after the exact candidate is loaded in Lab.

Open residuals after candidate review: #306 has no verified real issuer 3–5 peer set with aligned business models and fiscal periods; the actual source-derived probe is `INSUFFICIENT_COMPARABLE_PEERS`. #307 and #318 direct skill behavior was probed, but the integrated workflow remains blocked at `BLOCKED_CANONICAL_READ`. No live market-data ingestion, local Site code execution, release/production approval or canonical write occurred. These are recorded as partial/blocked, never inferred complete. Issues #423, #474, and #480 from aborted Iteration 06 remain open and are not accepted by this audit.
