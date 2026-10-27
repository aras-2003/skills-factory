# Strategy OS source and overlap review

Reviewed 2026-10-27 against the hash-pinned corpus in `strategy-source-manifest.json` and `strategy-source-file-index.csv`. The per-file index is authoritative for archive member paths and SHA-256 values. The seven downloaded ZIPs matched the prior register exactly; source archive SHA-256 values are recorded there.

## Corpus inventory and rights disposition

| Source | Inventory | Rights disposition | Strategy OS action |
|---|---:|---|---|
| Oria Tier-One Strategy | 50 `SKILL.md` files | No license file; a free download is not a redistribution license | Method reference only; write independently and do not copy prose/code |
| Oria 21 Strategy | 21 `SKILL.md` files | No license file | Method reference only; overlaps with Tier-One are one competency, not independent methods |
| Oria Excel Strategy | 21 `SKILL.md` files | No license file | Method reference only; Excel layout recipes are not calculation engines |
| `callmeramzo/mckinsey_skills` | 21 Markdown skills | No license file; community repository, not an official McKinsey artifact | Reject brand attribution; reference only |
| `MichaelRochonnn/mckinsey-bcg-consulting` | 76 `SKILL.md` files plus hub/docs | No license file; community repository, not an official McKinsey or BCG artifact | Reject brand attribution; reference only |
| `abinauv/business-consulting` | 16 `SKILL.md` files | MIT license included | Reuse only with preserved notice; no content copied in this change |
| `yoichiojima-2/consultant` | 1 router skill and 18 methodology Markdown files | MIT license included | Reuse only with preserved notice; not an Accenture or Bain source |

The corpus contains 350 files. The Oria packages contain 92 skills across three overlapping packs; they are not 92 distinct competencies. No third-party archive content is included in this repository.

## Competency mapping

| Issue | Exact source members (archive path; SHA in file index) | Existing Skills Factory overlap | Decision and implementation boundary | Behavior score |
|---|---|---|---|---|
| #446 Market sizing, segmentation, white space | Oria Tier-One: `skills/market-sizing/SKILL.md`, `skills/customer-segmentation/SKILL.md`, `skills/white-space-mapping/SKILL.md`; Oria Excel: `skills/tam-sam-som-model/SKILL.md`; Oria 21: `skills/customer-segmentation/SKILL.md` | `commerce/opportunity/market-transferability-review` covers transfer across markets; `investing/market-opportunity-scan` covers investment discovery, not strategy market sizing | Adapt as separate bounded strategy workflows. Reuse the existing transferability handoff. Keep top-down and bottom-up estimates separate, disclose assumptions/ranges, and block unsupported estimates. No imported methodology text. | N/O until fixtures and Site host behavior are run |
| #447 Profit pools and value drivers | Oria Tier-One: `skills/profit-pool-analysis/SKILL.md`, `skills/value-driver-tree/SKILL.md`, `skills/capital-allocation/SKILL.md`; Oria 21: `skills/profit-pool-analysis/SKILL.md`; Oria Excel: `skills/bridge-waterfall-constructor/SKILL.md` | `commerce/economics/unit-economics-review` computes offer-level contribution; `oaf/portfolio-execution/portfolio-prioritization` ranks initiatives | Add strategy-level profit-pool decomposition and a deterministic value-driver bridge. Do not reuse e-commerce VAT/CAC semantics for enterprise economics. Leave capital allocation to the portfolio prioritization handoff. | N/O until fixtures and Site host behavior are run |
| #448 Financial decision models | Oria Excel: `skills/dcf-structure-builder/SKILL.md`, `skills/three-scenario-model/SKILL.md`, `skills/sensitivity-tornado/SKILL.md`, `skills/formula-audit-checker/SKILL.md` | `investing/valuation-scenario-review` reviews security valuation assumptions but does not calculate generic business cash-flow models | Add a typed deterministic financial calculator; keep scenario selection, formula audit and sensitivity ranges tied to explicit inputs. Reuse decimal and missing-input principles, not investment-specific valuation assumptions. | N/O until formula fixtures and Site host behavior are run |
| #449 Benefits realization and capital allocation | Oria Tier-One: `skills/value-realization/SKILL.md`, `skills/capital-allocation/SKILL.md`; Oria Excel: `skills/kpi-dashboard-structurer/SKILL.md`; community reference: `skills/05-risk-performance-and-value-governance/value-realization.md` | `oaf/evidence-adaptation/evidence-loop-review`, `oaf/evidence-adaptation/kpi-quality-review`, `oaf/direction-strategy/strategy-to-execution-diagnostic`, and `oaf/portfolio-execution/portfolio-prioritization` | Add a benefit ledger/realized-versus-forecast reconciliation only. Hand off KPI quality, strategy execution diagnosis, decision rights and reallocation to existing OAF skills. Never duplicate capital allocation or generic KPI design. | N/O until fixtures and Site host behavior are run |
| #450 Source, license, duplication and benchmark audit | All 350 members in the seven ZIPs, exact per-file hashes in `strategy-source-file-index.csv` | Canonical Skills Factory/OAF catalog is the internal baseline | Archive-byte hashes and member hashes verified; license disposition and competency map recorded. Golden, negative and adversarial behavioral comparisons are not yet executed; no source is promoted based on inventory alone. | N/O for behavioral quality benchmark |

## Score rubric

Keep two independent 1–5 ratings per competency: **method fit** (does the method fit the stated decision and evidence?) and **behavioral implementation** (does the host produce correct outputs, block missing inputs, and survive adversarial/near-miss prompts?). `N/O` means the corresponding evidence has not been collected; it is not a zero or a pass. No ratings are assigned in this register because the runtime comparisons are not complete.

Every candidate's eval fixture must cite the source archive ID, exact member path and member SHA from the file index, the accepted/rejected method boundary, and expected behavior. Runtime receipts must identify model, date, exact Site source revision, prompt hash, result, and reviewer score. Static source, architecture and package checks cannot replace that evidence.
