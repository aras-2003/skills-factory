# Investment Factory capability inventory and CREATE gate

**Issue:** #755, A2, read-only discovery/design.  
**Baseline source:** `f9dc31cdd35a323cf30006c8a91a2a48af281188`.  
**Inventory generated from source:** 15 skills, 7 registered workflows. See [the generated source inventory](capability-source-inventory.generated.md).  
**Acceptance status:** PARTIAL — #297 DomainResult and #321 regression-contract dependencies remain open; no owner signoff for finance extraction; this report does not authorize skill creation or source mutation.

## Source inventory and channel evidence

Regenerate the source-only inventory table by running:

```bash
python3 scripts/investing/build_capability_inventory.py \
  --source-revision f9dc31cdd35a323cf30006c8a91a2a48af281188 \
  --output docs/investing/capability-source-inventory.generated.md
```

The generator reads `skills/investing/**/SKILL.md`, `workflows/runtime-registry.yaml` and `provenance/registry.yaml`; it validates source SHA-256 values and never infers runtime availability. The generated table is a snapshot, not a parallel source catalog.

The exact Cloud Next Lab catalog observed in this review reports source revision `f9dc31cdd35a323cf30006c8a91a2a48af281188`, release `1.38.575`, and lists all 15 source skills. This proves catalog listing in that Lab artifact, not successful skill execution or production installation. The committed `docs/catalog.json` identifies source revision `bfe038b44cd8`, and the committed Lab release manifest identifies older versions for several skills; both are stale relative to the baseline and are not used as channel evidence. All seven workflows declare `plugin=supported`, `lab=supported`, `chatgpt-zip=unavailable` in the baseline runtime registry. These are source declarations, not independent runtime receipts.

## Producer, consumer and state boundaries

| Producer / owner | Current responsibility | Main consumers | Evidence path / regression owner |
|---|---|---|---|
| `security-underwriting` | Issuer research and financial interpretation; one financial-quality owner | `investment-security-review`, opportunity/review workflows | `skills/investing/security-underwriting/scripts/financial_quality.py`; `tests/investing/test_financial_quality.py` |
| `valuation-scenario-review` | DCF/scenario card, peer comparability and valuation synthesis | `investment-security-review`; opportunity/review composition | `skills/investing/valuation-scenario-review/scripts/valuation_scenarios.py`, `peer_comparison.py`; skill tests |
| `technical-structure` | Descriptive OHLCV swing/pivot/trend structure; consumes supplied adjusted data | Current Lab candidate branch of `investment-os-review`; future #756 pilot | `skills/investing/technical-structure/scripts/engine.py`; `skills/investing/technical-structure/tests/test_engine.py` |
| `market-opportunity-scan` | Opportunity screening/ranking; no separate scheduler | `investment-opportunity-hunter`, `investment-theme-discovery` | `workflows/investment-opportunity-hunter/tests/cases.yaml`; #360 |
| `trend-theme-research` | Theme/value-chain research and qualitative signals | `investment-theme-discovery`, optional opportunity analysis | `workflows/investment-theme-discovery/WORKFLOW.md`; existing skill cases |
| `portfolio-state-review` | Read-only derived portfolio/exposure analysis | Portfolio review/observation, attention and sizing | Existing workflow cases; no canonical state mutation |
| `position-sizing-review` | Policy-aware sizing semantics; blocks on missing policy/critical evidence | Security review after issuer/portfolio gates | Existing skill cases; #321 regression scope |
| `thesis-challenge` / `thesis-monitor` | Falsification/invalidation and monitoring triggers | Security, portfolio and attention workflows | Existing skill cases and investment workflow cases |
| `investment-record-store` | Canonical reads and approval-specific append/write boundary | All workflows that need persisted thesis/decision/portfolio state | Supabase/store contracts; no parallel store |
| `decision-journal-update` / `investment-policy-design` | Append-only decision update / investor policy design | `investment-os-review`, security and portfolio review | Existing cases; retain owner authorization |

Workflow composition from the canonical registry: `investment-os-review` is the front door; opportunity hunter composes scanner/store plus optional analysis; theme discovery composes trend/scanner/store; portfolio observation and review compose state/monitor/store; attention review composes triage/store; security review composes underwriting/valuation/challenge/store and optional sizing. No consumer owns a second copy of another skill's formula or canonical state.

## Candidate dispositions and six CREATE gates

Gate keys: **G1** distinct triggers/non-triggers; **G2** distinct method; **G3** useful typed output for at least two consumers or essential risk boundary; **G4** one owner per formula/validation; **G5** typed input/output and evidence/as-of/failure rules; **G6** executable positive, negative, edge, adversarial and deterministic/reference tests. Only six PASS results permit CREATE. **UNKNOWN is not PASS.**

| Candidate | Existing owner / disposition | G1 | G2 | G3 | G4 | G5 | G6 | Decision and evidence gap |
|---|---|---|---|---|---|---|---|---|
| Financial performance / FCF quality | REUSE `security-underwriting` / `financial_quality.py` | FAIL | FAIL | UNKNOWN | PASS | UNKNOWN | PASS | Existing CFO−capex, FCF conversion and ROIC code/tests; no duplicate. |
| Capital efficiency / allocation | REUSE `security-underwriting` / `financial_quality.py` | FAIL | FAIL | UNKNOWN | PASS | UNKNOWN | PASS | ROIC already owned; any extraction needs #297/#321 and adapter proof. |
| Competitive position / moat / pricing | REUSE or EXTEND `security-underwriting` | FAIL | UNKNOWN | UNKNOWN | PASS | UNKNOWN | UNKNOWN | Existing underwriting covers business model and competitive position; no distinct testable method established. |
| Growth / operating dynamics | REUSE `security-underwriting` / `business_lifecycle.py` | FAIL | FAIL | UNKNOWN | PASS | UNKNOWN | PASS | Existing lifecycle/operating leverage analysis; preserve source tests. |
| Balance-sheet risk | REUSE `security-underwriting`; DCF bridge stays with valuation | FAIL | UNKNOWN | UNKNOWN | PASS | UNKNOWN | UNKNOWN | Keep issuer risk and valuation net-debt bridge ownership separate. |
| Management / governance | REUSE or EXTEND `security-underwriting` | FAIL | UNKNOWN | UNKNOWN | PASS | UNKNOWN | UNKNOWN | No separate independent output contract or method demonstrated. |
| Relative valuation / peer comparison | REUSE `valuation-scenario-review` / `peer_comparison.py` | FAIL | FAIL | UNKNOWN | PASS | UNKNOWN | PASS | #306/#524 coverage exists; avoid second peer owner. |
| Earnings revisions / expectations | REUSE underwriting, valuation and `thesis-monitor` | FAIL | UNKNOWN | UNKNOWN | PASS | UNKNOWN | UNKNOWN | #309 behavior is already embedded; preserve dated consensus and event-time rules. |
| Rerating / valuation scenario | REUSE `valuation-scenario-review` | FAIL | FAIL | UNKNOWN | PASS | UNKNOWN | PASS | Existing card/scenario method; no new skill needed. |
| Confirmed technical structure / setup | REUSE `technical-structure` + #319 discovery | FAIL | FAIL | UNKNOWN | PASS | UNKNOWN | PASS | Candidate technical skill; no claim of predictive edge. |
| Momentum / relative strength | CONDITIONAL pilot #756 after #753/#755 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | FAIL | No accepted method, typed output or out-of-sample evidence yet. |
| Volume / volatility specialist | NO-GO / defer | UNKNOWN | UNKNOWN | FAIL | UNKNOWN | UNKNOWN | FAIL | Distinct triggers, consumers and owner not established. |
| Market opportunity / ranking | REUSE `market-opportunity-scan` (#360) | FAIL | FAIL | UNKNOWN | PASS | UNKNOWN | PASS | Do not create another screener, ranking formula or scheduler. |
| Theme / value chain | COMPOSE `trend-theme-research` via theme workflow | FAIL | FAIL | UNKNOWN | PASS | UNKNOWN | PASS | Existing composition is the owner; no standalone duplicate. |
| ETF look-through / portfolio state | REUSE existing exposure and portfolio owners (#556) | FAIL | UNKNOWN | UNKNOWN | PASS | UNKNOWN | UNKNOWN | #556 owns look-through; portfolio state stays derived/read-only. |
| Sizing / policy | REUSE `position-sizing-review` + `investment-policy-design` | FAIL | FAIL | UNKNOWN | PASS | UNKNOWN | PASS | Policy input is not a new sizing formula or permission to trade. |
| Thesis challenge / monitoring / journal | REUSE challenge, monitor and journal skills | FAIL | FAIL | UNKNOWN | PASS | UNKNOWN | PASS | Keep invalidation, monitoring and append-only record semantics distinct. |
| New decision contract | COMPOSE in `investment-security-review`; specify in #754 after #753 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | FAIL | Not a new skill; #753/#754 and #297 output mapping remain unresolved. |
| Canonical store / state | REUSE `investment-record-store` | FAIL | FAIL | UNKNOWN | PASS | UNKNOWN | PASS | No second database/store; use current authorized read/write contract. |

Existing deterministic owners and tests: financial quality/ROIC/FCF — `security-underwriting/scripts/financial_quality.py`; lifecycle — `business_lifecycle.py`; DCF/scenario — `valuation_scenarios.py`; peer comparability — `peer_comparison.py`; OHLCV structure — `technical-structure/scripts/engine.py`; persistent state — `investment-record-store`. For technical momentum, #756 must define one formula owner, benchmark/currency/as-of and no-lookahead fixtures before CREATE. The candidate `technical-structure` v0.1.1 does not itself calculate momentum/relative strength/volume/volatility and remains non-production.

## Regression impact and blockers

- #297 defines the generic DomainResult consumer/export contract; #753 must map Investment SpecialistResult one-way into it. This dependency is OPEN.
- #321 is the cross-skill source/routing/correctness/E2E acceptance set; it must be mapped to candidate contracts and regression owners. This dependency is OPEN.
- #618 overlap matcher is closed; its current coverage still needs a source/consumer check against the proposed candidates.
- #383 is closed, but authenticated archive and runtime evidence remain incomplete; do not infer historical replay acceptance.
- #674/#680 XML migration may touch Investing skills concurrently; recheck paths/branch before any skill edit.
- No finance extraction, new skill, runtime change, store change or maturity promotion is authorized by this inventory.

**Disposition:** inventory design implemented as a source-bound report plus a deterministic generator; #755 remains **PARTIAL / NOT CLOSED** until #297/#321 reconciliation and owner signoff.