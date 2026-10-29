# Investment OS Review Workflow

## Purpose
Act as the default orchestration front door for natural investment requests. Route the request into the smallest evidence-backed Investment OS workflow that can answer it, rather than answering with generic investment commentary.

This workflow does not replace the specialist workflows. It selects and invokes them.

## Natural activation
Use this workflow when the user asks about their investments in ordinary language and does not explicitly name a narrower Investment OS workflow.

Typical requests include:
- "review my portfolio" / "review this portfolio";
- "what is happening with my portfolio?" / "what changed?" / "what should I watch?";
- "review this stock/security";
- "find opportunities" / "what should I research next?";
- "what investment themes are worth researching?";
- "does this news/event matter for my holdings?";
- "help me define my investment policy/risk limits."

Do not require the user to know Investment OS terminology, canonical storage, specialist names or workflow names.

## Runtime routing preflight
When the MCP tool `route_investment_request` is available, call it with the user's full natural-language request before substantive investment analysis. Preserve its returned `routing_receipt` in the execution trace; it proves routing only, not child execution.

Treat the returned `child_workflow` as the primary route when it is specific. If the tool returns `investment-os-review` / unknown, resolve the ambiguity with the routing matrix below rather than inventing a specialist result.

The routing tool is a classifier only. It does not replace loading and executing the selected child workflow.

## Routing matrix
Choose exactly one primary route unless the request genuinely contains two separate decisions.

### Portfolio observation route
Use `investment-portfolio-observation` when the user primarily wants:
- what changed since the previous snapshot;
- what is happening with current positions;
- exposure drift;
- what deserves attention or monitoring;
- a compact observation update without target-allocation optimisation.

Prefer observation when the decision object is "what changed / what should I watch" rather than "how should I restructure the portfolio".

### Portfolio review route
Use `investment-portfolio-review` when the request concerns:
- multiple holdings or portfolio weights;
- concentration, diversification, overlap, allocation or portfolio risk;
- current portfolio state, drift, policy fit or what requires attention;
- next portfolio-level decisions.

A prompt containing holdings/weights plus a request to review risk or next decisions MUST take this route.

### Security route
Use `investment-security-review` for one named security when the user wants end-to-end underwriting, valuation, thesis challenge, portfolio fit or sizing.

### Opportunity route
Use `investment-opportunity-hunter` when the user asks to scan for new securities/candidates or asks what to research next without a known security.

### Theme route
Use `investment-theme-discovery` for structural/cyclical investment themes, value chains or second-order beneficiaries.

### Attention route
Use `investment-attention-review` when the user brings new company/industry/market information and asks whether it changes prior theses or deserves deeper work.

Systemic and cross-asset market indicators (for example credit spreads, liquidity, breadth, real yields, or macro signals) are new market information. Use `investment-attention-review` first for vintage-aware, correlation-deduplicated materiality and direction triage. Delegate only evidenced portfolio exposure implications to `investment-portfolio-observation` or `portfolio-state-review`; do not turn a systemic indicator request into a generic historical replay or portfolio observation.

### Policy route
Use `investment-policy-design` when the decision is about portfolio rules, risk limits, target bands, sizing constraints or investment governance rather than reviewing current holdings.

### Clarify before routing
If the user refers to existing shares but does not specify whether they want an observation, a portfolio risk review, analysis of a named security, or policy help, ask one short question to establish the decision object. Do not offer HOLD / ADD / TRIM / EXIT (or equivalent actions) before that clarification. Ask for holdings, weights, or risk preferences only after the user selects a route.

For one named security, thesis, valuation, downside, portfolio fit or a stated position size belongs to security review. An incidental percentage for that security does not by itself make the task portfolio-wide. Use portfolio review when the user asks about concentration, diversification, exposure, overlap, or decisions across multiple holdings.

## Orchestration rules
1. Run the runtime routing preflight when available; otherwise use the routing matrix.
2. Select the primary route before doing substantive analysis and load the exact matching child workflow/skill by name.
3. Invoke the selected child workflow/skill and follow its evidence/canonical rules.
   - Count the child as executed only when a runtime execution receipt identifies the child workflow, execution status, and correlated run. A selected route, planned invocation, or prose claim is not proof that the child ran.
   - If routing succeeded but the exact child cannot be loaded or no child execution mechanism/receipt is available, return a blocked/not-run state and the missing runtime evidence; do not synthesize the child result or switch to a different specialist.
   - The final status must name the same child as the routing receipt. A different route is a stop condition requiring a corrected pre-analysis route, not an acceptable substitution.
4. Do not duplicate the child workflow with a generic answer before or after invocation.
5. If the portfolio route is selected:
   - canonical reads must be attempted by the child workflow;
   - user-supplied weights are evidence to reconcile, not a replacement for canonical state;
   - substantial chartable portfolio data must continue through integrated reporting and the visual-floor path.
6. If the request is ambiguous between routes, prefer the route that directly matches the user's decision object:
   - portfolio observation > change/drift/monitoring of existing holdings;
   - portfolio review > multiple holdings/weights plus risk, concentration, structure or decisions;
   - security > one named security;
   - attention > new event/news against existing holdings/theses;
   - opportunity > discovery of new securities;
   - theme > thematic research;
   - policy > rules/limits.
7. Do not fan out to every Investment OS workflow merely for completeness.
8. Missing evidence narrows the child workflow result; it does not justify bypassing the child workflow.

## Output contract
Return the selected child workflow's normal output. Do not add a separate router report.

When runtime diagnostics are explicitly requested, include:
- selected Investment OS route;
- selected child workflow;
- why that route matched the user's decision object.

## Stop conditions
Stop routing once one primary child workflow clearly owns the request.
Escalate to two routes only when the user explicitly asks two distinct investment decisions that cannot be answered by one child workflow.
