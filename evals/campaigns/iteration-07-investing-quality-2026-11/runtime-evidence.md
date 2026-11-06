# Iteration 07 candidate runtime evidence — 2026-11-06

## Identity and scope

- Canonical source / merged PR #587: `854117b7128dcc88e5c46407b8bee71309af7357`.
- Cloud Next Site: `Skills Factory Cloud Next`, private owner-only audience preserved.
- Site runtime: attestation `verified`; Lab `1.38.464`; release `1.38.464+854117b7128d`; canonical source `854117b7128dcc88e5c46407b8bee71309af7357`; deployed `2026-11-06T20:24:21Z`.
- Runtime mode: `host_model_executes_loaded_instructions`. Python helpers are packaged but the runtime reports `supporting_code_execution=not_executed`; the figures below were calculated from reviewed inputs using the displayed formulas. No claim that a packaged Python helper ran on Site.
- Release approval remains false. No canonical reads/writes, portfolio mutation, trade, maturity change, or production promotion was performed.

Runtime tool-call receipts are unsigned records. They identify calls and package/source hashes; they do not certify semantic correctness of the model response.

| Call | Result / identity | Completed (UTC) | Input SHA-256 | Output SHA-256 |
|---|---|---|---|---|
| `runtime_info` | `verified`, exact source and Lab above | 20:48:29.324 | `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a` | `53a259a6c242e5d405cdc6b91d04c5a29a7447f14bc6ab47b129fae2a7ab4613` |
| `load_skill: security-underwriting` | v0.5.3, content `733f6ea72cc857d4977536cbac747f643cdec0a13d297e2e67885f5ec2f98c61` | 20:48:29.321 | `af41cbe400ff54bb0e6357300fd4b738fe17fb72b112a2035935faa344d5ef3f` | `591ad3d8265fdc512347cdb3de719a5d8e6e201a7f2d51d1d158fc7e2a99b093` |
| `load_skill: valuation-scenario-review` | v0.3.1, content `cd9bdb6e1738874eca5ab79b4ad4b92d9d993b0f3733d808ea33592f6782f53d` | 20:48:29.174 | `852741e448df6cfcd19556fd7de0cbcca74d3ab8168fb75915c295f5a62a61e2` | `32cf0c9eb6cad96d6c222c6bf7795a7cad30731dffdeefc4b57a812290aa912e` |
| `load_skill: thesis-challenge` | v0.1.2, content `850c9ae554346b3c0acecf37d968026e2e9390c5c0ff098e8d6a670c975532b2` | 20:48:29.237 | `8417dd7d74f0339e0b1d66b8936a821f5ac04306b0c6531f213327f700f3fc50` | `bf61691bc41160fd782358afcbbcb25a6da6e131ac7d4efb04a3ca396e5fab57` |
| `route_investment_request` | `security-review` → `investment-security-review`; routed only | 20:47:34.082 | `355900207b8163943d1bf78ce859573cd510ecfd58693091d3aff4dee549344d` | `e21959c733cbd9648b3d1bd1bae373360c1618765e714171656457f0e1acd062` |
| `load_skill: investment-security-review` | v0.4.4, content `cea0256cabe61c35573b006dc24d280d2e1adced9210cdb288fd83a51afbe074` | 20:48:29.203 | `95524b2c75374b6cfce3ded2fbdae97a908541e91b3b81f34b0f84808aabb0bf` | `fcce1277ff15ed852f641c7236f8301dd2800aa1ef06ba7d12976dd2a85f15b1` |

The route's `workflow_executed=false` is significant. The exact workflow declares `investment-record-store` a required dependency and says a missing/inaccessible canonical read must return `BLOCKED_CANONICAL_READ`, never an assumed empty history. That tool is absent from this runtime's capabilities. In accordance with Iteration 07's exclusion of live portfolio reads/writes, the workflow was stopped at that gate. This is an integration blocker, not a successful end-to-end workflow result.

## #318 — source-backed financial quality probe (AMD)

**Probe input:** assess source/as-of gates, periods, units, FCF and conversion, working capital, debt/cash, dilution and cycle flags for AMD using public filings available by 2026-11-06. Do not value or size.

**Source contract:** USD millions unless stated; GAAP consolidated continuing operations for cash flow and income where available; FYs ended Dec 30, 2023, Dec 28, 2024, and Dec 27, 2025; latest YTD ended Sep 26, 2026 compared with same nine months ended Sep 27, 2025. The 2026 10-Q was signed Nov 3, 2026. The 2025 10-K contains the three annual periods and was filed in February 2026. No FX conversion or missing-value backfill.

### Period-aligned facts and derived values

| Period | Revenue | Gross margin | Continuing net income | Continuing CFO | PP&E purchases | FCF = CFO − capex | FCF / positive continuing NI |
|---|---:|---:|---:|---:|---:|---:|---:|
| FY2023 | 22,680 | 46.1% | 854 | 1,667 | 546 | 1,121 | 131.3% |
| FY2024 | 25,785 | 49.4% | 1,641 | 3,041 | 636 | 2,405 | 146.6% |
| FY2025 | 34,639 | 49.5% | 4,269 | 6,493 | 974 | 5,519 | 129.3% |
| 9M ended 2025-09-27 | 24,369 | 47.5% | 2,649 | 4,189 | 752 | 3,437 | 129.7% |
| 9M ended 2026-09-26 | 35,166 | 53.5% | 6,105 | 6,523 | 1,845 | 4,678 | 76.6% |

Annual values are reported in AMD's 2025 10-K; interim facts in the Q3 2026 10-Q. Gross margins for 9M are gross profit divided by revenue (11,575/24,369 and 18,829/35,166). FCF values use continuing CFO less cash PP&E purchases; this is not adjusted for leases or other capital commitments. Continuing income avoids mixing FY2025 discontinued ZT income ($66m) and 9M 2025 discontinued income ($175m) into the conversion denominator.

The YTD profile is mixed: revenue +44.3% YoY; continuing CFO +55.7%; PP&E cash purchases +145.3%; FCF +36.1%; and FCF conversion fell from 129.7% to 76.6%. The ratio is sensitive to non-cash items and tax: 9M 2026 included a $1.179bn non-cash customer-warrant adjustment in CFO reconciliation and a $918m discrete stock-compensation tax benefit. These are visible items, not silently normalized earnings.

At Sep 26, 2026 AMD reported cash and short-term investments of $15.776bn and long-term debt of $7.079bn, net cash of $8.697bn on that restricted definition; lease liabilities and guarantees are additional exposures. Continuing CFO reflected $3.6bn net operating-asset/liability outflows, including inventory $3.543bn, receivables $2.894bn and prepaid/other assets $2.061bn, partially offset by $4.483bn higher accounts payable. This is a cash-conversion watch item while Data Center revenue grows.

Dilution context: 9M diluted weighted-average shares were 1.657bn versus 1.632bn (+1.5%); stock-based compensation was $1.513bn versus $1.152bn (+31.3%). ROIC is **N/M** because this probe did not establish a consistent sourced NOPAT and average invested-capital series. A complete debt maturity/coverage analysis and 12–20-quarter KPI context were not produced in this bounded acceptance probe; no lifecycle classifier or renderer was invoked. Accordingly this is a real-source financial-quality probe, not a complete integrated security-underwriting report.

**Outcome:** source provenance, same-quarter YTD, unit discipline and FCF arithmetic pass for the listed fields. Cash conversion and increased capex/working capital warrant `WARN`; no “healthy” or normalized-run-rate claim. ROIC and unsupplied metrics remain N/M. No valuation, sizing, canonical read/write or trade.

## #307 — thesis challenge probe (AMD)

**Supplied baseline thesis:** “Continued AI/Data Center growth can sustain elevated market expectations.” It is treated as a user-supplied hypothesis, not an established fact. The integrated workflow was blocked at the canonical-read gate described above; the following is a separate direct execution of the packaged `thesis-challenge` instructions against the supplied thesis and cited public facts only.

1. **Working-capital and capex conversion (strongest; UNRESOLVED).** 9M revenue and continuing CFO rose, but PP&E purchases grew faster and FCF conversion fell to 76.6%. Management attributed $3.6bn of working-capital cash outflow principally to inventory, receivables and supplier prepayments. If data-center demand or shipment timing decelerates after inventory/prepayments are committed, cash conversion, inventory risk and returns on capacity could worsen; no source supports a numerical downside range. Contradictory evidence: 9M revenue +44.3%, CFO +55.7%, FCF remains positive and rose +36.1%. Disconfirming evidence: subsequent quarters convert the current inventory/receivable build into collections and shipments without persistent FCF-conversion deterioration.
2. **Commercial-partner guarantees and customer-linked warrants (UNRESOLVED).** At Sep 26, 2026 AMD disclosed up to $7.7bn gross data-center lease-guarantee exposure over terms up to 15 years and $750m commercial-partner debt guarantees up to six months; no partner was in default and no amounts had been paid. It also disclosed $4.5bn unrecognized grant-date fair value on customer warrants to be recorded as a revenue reduction as qualifying customer revenue is recognized; no shares had vested/exercised. Partner distress could create lease/debt obligations, while warrants reduce recognized revenue and can dilute if conditions vest. Maximum exposures are not expected losses; no probability or valuation impact is derived. Disconfirming evidence: falling guarantee balances/termination, no defaults, customer revenue achieved with transparent recognized warrant accounting and no sustained margin/cash deterioration.

No third objection is forced. A dated price/consensus snapshot exists in secondary QDD Research (Nov 5, 2026), but it does not establish what expectations are embedded in price or offer a decision-grade scenario; this probe does not equate consensus targets with fair value. Business thesis state: **WEAKENED at the cash-conversion and partner-commitment assumptions, not invalidated**. Valuation, timing and portfolio-sizing conclusions remain untested. No trade instruction.

## #306 — issuer peer-comparison probe (AMD, MU, MSFT)

**As-of:** Nov 5, 2026; single secondary data source QDD Research for quote/EV and consensus snapshot. Raw FY2027 fields are transcribed below for diagnostic display, not treated as aligned peers. Fiscal year ends differ (AMD Dec 31, MU Aug 31, Microsoft Jun 30); QDD's forward multiples use next-fiscal-year estimates, so that row label does not establish a common forward period. Financial-cycle economics and business models also differ.

| Issuer | Business model | Close | EV | FY2027 consensus sales / EV-sales | EBITDA / EV-EBITDA | EPS / P-E | Comparison disposition |
|---|---|---:|---:|---:|---:|---:|---|
| AMD | Fabless high-performance compute, AI accelerators, CPUs, GPUs, embedded | $404.40 | $651.5bn | $95.396bn / 6.8x | $35.842bn / 18.2x | $17.53 / 23.1x | Target; its Dec fiscal period differs from peer fiscal-year periods |
| MU | Integrated DRAM/NAND memory producer; highly cyclical | $656.39 | $704.4bn | $276.194bn / 2.6x | $246.546bn / 2.9x | $173.76 / 3.8x | Exclude as direct AMD peer: memory cycle/product economics differ; FY ends Aug 31 |
| MSFT | Cloud/software/services platform | $535.93 | $4.02tn | $396.033bn / 10.2x | $244.007bn / 16.5x | $20.02 / 26.8x | Exclude: different software/cloud model; FY ends Jun 30 |

The table is descriptive of source observations, **not apples-to-apples**. NTM valuation charts are described by QDD but numeric NTM values were not publicly exposed on the reviewed pages. More importantly, there is only one clearly direct AI-accelerator peer (NVDA); AVGO and MRVL have partial datacenter AI/ASIC/network exposure but mixed software/IP or broader data-infrastructure economics. Their company-level metrics cannot be asserted comparable to AMD merely because the vendor assigns the same broad semiconductor sector. The same-source FY2027 annual forecasts cannot repair differing fiscal periods; 3–5Y EPS CAGR is not present in this public snapshot, so PEG is N/M.

For an offline deterministic-helper probe (not a Site tool execution), `peer_comparison.py` received AMD plus MU, Microsoft, NVDA, AVGO and MRVL snapshots dated Nov 5, 2026. Source-reported forward EV/Sales was included only where observed (AMD 6.8x, MU 2.6x, Microsoft 10.2x, NVDA 10.5x, MRVL 9.8x); AVGO's FY2027 value was left missing because it was not exposed in the reviewed page output. Each candidate had its explicit business-model label and actual vendor fiscal-year period. The helper returned `INSUFFICIENT_COMPARABLE_PEERS`, `included_peer_count=0`, all five peers excluded (four `BUSINESS_MODEL_MISMATCH`, Microsoft `SECTOR_OR_INDUSTRY_MISMATCH`), empty plot points, `recommendation=null`, `ranked=false`, snapshot ID `8cf4a0c11f659c232ee6b645e6555ef266e9133fc8968a096f1bd35d9213acab`. Thus it did not silently compare mismatched FY periods or unlike business models. The Site runtime itself loaded the exact skill but does not expose this Python helper for execution. No BUY rank or recommendation.

This is the intended safe behavior against false comparability but **does not satisfy** #306's acceptance requirement for a reproducible apples-to-apples 3–5-peer table for AMD and MU. A sufficient same-snapshot, period-aligned, economically comparable real peer dataset remains missing.

## Integrated-runtime acceptance and remaining blockers

- Route smoke succeeded for one named issuer and selected `investment-security-review`; no specialist was invoked by the router.
- Required `investment-record-store` capability is not present in the current Site runtime. The integrated workflow therefore correctly stops at `BLOCKED_CANONICAL_READ`; direct skill probes do not turn the integrated workflow into PASS.
- #318 has the source-backed calculations above plus passing synthetic regression suites, but the end-to-end integrated workflow is still blocked by the missing canonical-read tool; full security review requirements (history, lifecycle, renderer, debt coverage) were outside this probe.
- #307 direct challenge behavior was exercised with two evidence-backed countercases and no fabricated third; the integrated workflow remains blocked at its required context read.
- #306 remains **BLOCKED** on a real-source, compatible 3–5 peer cohort and complete runtime acceptance. Do not close it based on synthetic fixtures or N/M output alone.
- #231 source inventory is complete, but the now-observed required-tool gap must be reflected in its audit and routing residual.
- No deployment, merge, or issue status was changed as part of this follow-up evidence capture.

## Sources

- AMD 2025 Form 10-K, filed Feb 3, 2026, fiscal years ended Dec 30, 2023, Dec 28, 2024, Dec 27, 2025: https://www.sec.gov/Archives/edgar/data/2488/000000248826000018/amd-20251227.htm. The Feb 4 10-K/A corrected MD&A presentation and did not restate the financial statements: https://www.sec.gov/Archives/edgar/data/2488/000000248826000021/amd-20251227.htm
- AMD Q3 2026 Form 10-Q, nine months ended Sep 26, 2026, signed Nov 3, 2026: https://www.sec.gov/Archives/edgar/data/2488/000000248826000191/amd-20260926.htm
- Micron 2026 Form 10-K, year ended Sep 3, 2026, signed Oct 9, 2026: https://www.sec.gov/Archives/edgar/data/723125/000072312526000023/mu-20260903.htm
- QDD Research AMD, MU, Microsoft, NVIDIA, Broadcom, Marvell reports, all dated Nov 5, 2026: https://www.qddresearch.com/us/amd/ ; https://www.qddresearch.com/us/mu/ ; https://www.qddresearch.com/us/msft/ ; https://www.qddresearch.com/us/nvda/ ; https://www.qddresearch.com/us/avgo/ ; https://www.qddresearch.com/us/mrvl/ . Secondary vendor source, used for same-date context/consensus only; definitions and forecast periods remain subject to the limitations above.
