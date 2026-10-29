# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mcp==2.3.0",
# ]
# ///

from __future__ import annotations

import re

from mcp.server import MCPServer

SERVER_INSTRUCTIONS = """
Investment OS runtime guardrail.

For any user request whose decision object is investments, a portfolio, holdings,
stocks, securities, ETFs, investment themes, investment opportunities, investment
policy/risk limits, or new information about an existing investment:

1. Before substantive investment analysis, call route_investment_request with the
   user's full request. This call is the auditable front-door routing receipt.
2. Load the returned child_workflow by its exact packaged name before analysis;
   the route result alone is not execution. If it cannot be loaded, stop and state
   that the workflow did not run. Do not silently substitute another specialist.
   If next_action is load_front_door_then_clarify, load the front door and ask the
   user to clarify before any substantive analysis or recommendation.
3. Follow the loaded workflow's sequence and evidence gates. Do not claim that a
   child workflow ran unless its own load/execution is present in the tool trace.
4. Do not replace the selected workflow with generic investment commentary.
5. For portfolio requests:
   - observation/change/monitoring intent -> investment-portfolio-observation;
   - full risk/concentration/decision review -> investment-portfolio-review.
6. This router does not make buy/sell decisions. It only chooses the Investment OS
   workflow that owns the request.

Do not call this router for unrelated finance questions such as banking mechanics,
tax explanations, mortgages, budgeting, or generic accounting unless the request is
specifically an Investment OS decision.
""".strip()

mcp = MCPServer(
    "Arek Investment OS runtime",
    description="Routes natural investment requests into the correct Investment OS workflow before analysis.",
    instructions=SERVER_INSTRUCTIONS,
)


def _contains(text: str, *phrases: str) -> bool:
    return any(p in text for p in phrases)


def _ticker_count(text: str) -> int:
    # Conservative heuristic: uppercase security-like tokens only.
    tokens = re.findall(r"\b[A-Z]{2,5}\b", text)
    stop = {
        "ETF", "ETFS", "AI", "USD", "PLN", "EUR", "CEO", "CIO", "CTO",
        "PE", "EPS", "FCF", "DCF", "ROIC", "TAM", "CAGR",
    }
    return len({token for token in tokens if token not in stop})


@mcp.tool()
def route_investment_request(user_request: str) -> dict[str, str | bool]:
    """Call before substantive analysis for natural investment requests.

    Routes portfolio observation/change monitoring, full portfolio review,
    one-security review, new-opportunity discovery, investment-theme research,
    new-information attention triage, or investment policy/risk-limit design
    into the matching Investment OS child workflow.
    It does not provide investment advice or replace the selected workflow.
    """
    raw = user_request.strip()
    # Strong, explicit non-investment task forms take precedence over words
    # quoted in a scope exclusion (for example, "No investment analysis").
    if re.match(
        r"^(?:fix|correct|proofread|edit)\s+(?:(?:only|just)\s+)?(?:the\s+)?(?:punctuation|grammar|spelling)\b",
        raw,
        flags=re.IGNORECASE,
    ):
        return {
            "is_investment_request": False,
            "route": "not_applicable",
            "child_workflow": "investment-os-review",
            "reason": "request is limited to a non-investment editing task",
            "must_invoke_child_workflow": False,
        }
    # Route the requested task, excluding clauses that explicitly reject an
    # alternative (for example "not my portfolio" or "nie ... rebalancingu").
    text = re.sub(r"\b(?:do not|don't|not|without|nie)\b[^.!?;,\n]*", "", raw.lower())

    if not raw:
        return {
            "is_investment_request": False,
            "route": "unknown",
            "child_workflow": "investment-os-review",
            "reason": "empty request; no investment decision object detected",
            "must_invoke_child_workflow": False,
        }

    non_investment_finance = _contains(
        text,
        "mortgage", "mortgages", "fixed-rate loan", "fixed rate loan",
        "bank account", "banking mechanics", "budgeting", "household budget",
        "tax filing", "tax explanation", "generic accounting",
        "kredyt hipoteczny", "hipoteka", "konto bankowe", "budżet domowy",
        "budzet domowy", "rozliczenie podatku", "wyjaśnienie podatku",
        "wyjasnienie podatku", "księgowość", "ksiegowosc",
    )
    explicit_investment_context = _contains(
        text,
        "investment", "investing", "portfolio", "stock", "stocks", "security", "securities",
        "etf", "fund", "holdings", "investment policy", "risk limit",
        "inwestyc", "portfel", "spół", "spolk", "akcj", "fundusz",
        "share", "thesis", "gross margin", "marża brutto", "marza brutto", "watchlist",
        "research candidates", "kandydatów do researchu", "kandydatow do researchu", "opportunit", "okazj",
    )
    if non_investment_finance and not explicit_investment_context:
        return {
            "is_investment_request": False,
            "route": "not_applicable",
            "child_workflow": "investment-os-review",
            "reason": "request concerns personal finance or accounting, not an Investment OS decision",
            "must_invoke_child_workflow": False,
        }

    policy = _contains(
        text,
        "investment policy", "portfolio policy", "risk limit", "risk limits",
        "maximum position", "max position", "position limit", "sector limit",
        "rebalancing rule", "rebalancing rules", "zasady portfela",
        "limit jednej spółki", "limity sektorowe", "rebalancing",
        "maksymalny udział", "reguły portfela",
    )
    systemic_risk_triage = _contains(
        text,
        "systemic risk", "cross-asset", "cross asset", "credit condition",
        "credit spread", "market breadth", "real yield", "macro condition",
        "macro indicator", "liquidity indicator", "risk indicator",
    ) and _contains(
        text,
        "triage", "assess", "review", "monitor", "indicator", "signal",
        "ocen", "przejrz", "monitoruj", "sygnał", "sygnal",
    )
    attention = systemic_risk_triage or _contains(
        text,
        "new information", "new news", "does this news", "does this change the thesis",
        "changes the thesis", "materiality", "headline", "nowe informacje",
        "zmieniają tezę", "zmienia teze", "czy to zmienia", "wymaga głębszej analizy",
        "wymaga glebszej analizy", "give attention", "attention next", "next research",
        "research next", "attention review",
    ) or ("watchlist" in text and _contains(text, "earnings", "results", "news", "information", "wynik", "informacj"))
    # Event triage must outrank the portfolio keyword when the request asks
    # whether one named holding's earnings deserve thesis attention.
    if (
        _contains(text, "earnings", "wynik", "results")
        and _contains(text, "thesis", "tez", "holding", "portfolio", "portfel", "my company", "spółki", "spolki")
        and (
            _contains(
                text,
                "attention", "uwag", "warrant", "matter", "deserve", "wymag",
                "change", "changes", "changed", "impact", "affect", "influence",
                "zmienia", "wpływ", "wplyw",
            )
            or (
                _contains(text, "after earnings", "after results", "po wynik")
                and _contains(text, "check", "review", "assess", "sprawd", "przejrz", "ocen")
            )
        )
    ):
        attention = True
    theme = _contains(
        text,
        "investment theme", "investment themes", "theme research", "value chain",
        "second-order", "structural theme", "cyclical theme", "temat inwestycyjny",
        "tematy inwestycyjne", "łańcuch wartości", "lancuch wartosci",
    )
    opportunity = _contains(
        text,
        "find opportunities", "find stocks", "new stocks", "new securities",
        "research candidates", "what should i research", "scan for",
        "znaleźć kilka nowych spółek", "znalezc kilka nowych spolek",
        "nowe spółki", "nowe spolki", "kandydatów do researchu",
        "kandydatow do researchu", "co warto zbadać", "co warto zbadac",
        "watchlist screen", "screen my watchlist", "screen watchlist",
        "preview the screen", "preview-only screen", "screen these candidates",
        "promising opportunities", "promising opportunity", "obiecujące okazje", "obiecujace okazje",
        "okazje w sektorze", "opportunities in the renewable", "opportunities in sector",
    )
    observation = _contains(
        text,
        "what is happening with my portfolio", "what changed in my portfolio",
        "what changed", "what should i watch", "monitor my holdings",
        "monitor my portfolio", "portfolio drift", "observe my portfolio",
        "co się dzieje z portfelem", "co sie dzieje z portfelem",
        "co się zmieniło", "co sie zmienilo", "co zmieniło się", "co zmienilo sie",
        "warto obserwować", "warto obserwowac", "co mam obserwować",
        "co mam obserwowac", "obserwuj moje pozycje", "obserwuj portfel",
        "zmiany w portfelu", "monitoruj portfel",
    )
    portfolio = bool(re.search(r"\breview\s+(?:my|this|the)\s+investment\s+portfolio\b", text)) or _contains(
        text,
        "my portfolio", "this portfolio", "portfolio review", "review portfolio",
        "portfolio risk", "portfolio concentration", "portfolio diversification",
        "holdings", "weights", "allocation", "top 2", "top 5", "other holdings",
        "etf overlap", "what requires attention", "review my portfolio", "portfel", "moj portfel",
        "mój portfel", "wagi", "udziały", "udzialy", "koncentracja",
        "dywersyfikacja", "pozycje w portfelu",
    )
    single_security_intent = (
        _contains(text, "stock", "security", "company", "issuer", "spółk", "spółce", "spolce", "spolk", "akcj", "good investment")
        and (
            re.search(r"(?:review|assess|analy[sz]e|analiz|oceń|ocen|wyceń|wycen).{0,60}(?:stock|security|company|issuer|spółk|spółce|spolce|spolk|akcj)", text)
            or _contains(text, "thesis", "tez", "valuation", "underwriting", "good investment")
        )
    )

    # Multiple security-like tickers plus weights/percentages strongly indicates portfolio.
    if _ticker_count(raw) >= 2 and ("%" in raw or portfolio):
        portfolio = True

    # This endpoint is an investment router, not a universal ambiguity
    # resolver. Do not misroute unrelated prompts just because they contain a
    # financial word in a negation, quoted string or explanation.
    if not explicit_investment_context:
        return {
            "is_investment_request": False,
            "route": "not_applicable",
            "child_workflow": "investment-os-review",
            "reason": "no investment decision object was identified",
            "must_invoke_child_workflow": False,
        }

    # Ordering reflects decision ownership, not business priority.
    if policy:
        route, child, reason = (
            "policy",
            "investment-policy-design",
            "request is about portfolio rules, limits or rebalancing policy",
        )
    elif attention:
        route, child, reason = (
            "attention",
            "investment-attention-review",
            "request asks whether new information changes an existing investment thesis or deserves escalation",
        )
    elif single_security_intent and not (_ticker_count(raw) >= 2 and "%" in raw):
        route, child, reason = (
            "security",
            "investment-security-review",
            "one security's thesis, valuation or portfolio fit is the decision object",
        )
    elif observation:
        route, child, reason = (
            "portfolio_observation",
            "investment-portfolio-observation",
            "request asks to observe portfolio changes, drift or what deserves attention without requiring target-allocation optimisation",
        )
    elif portfolio:
        route, child, reason = (
            "portfolio",
            "investment-portfolio-review",
            "request concerns multiple holdings, weights, concentration, diversification or portfolio-level decisions",
        )
    elif theme:
        route, child, reason = (
            "theme",
            "investment-theme-discovery",
            "request is about structural/cyclical themes or value-chain research",
        )
    elif opportunity:
        route, child, reason = (
            "opportunity",
            "investment-opportunity-hunter",
            "request asks to discover new securities or research candidates",
        )
    elif _ticker_count(raw) == 1 or _contains(
        text,
        "review this stock", "review this security", "review the stock",
        "stock thesis", "security review", "wyceń spółkę", "wycen spolke",
        "oceń spółkę", "ocen spolke", "analiza spółki", "analiza spolki",
    ):
        route, child, reason = (
            "security",
            "investment-security-review",
            "one named security is the clear decision object",
        )
    else:
        return {
            "is_investment_request": True,
            "route": "unknown",
            "child_workflow": "investment-os-review",
            "reason": "investment intent detected but the decision object is ambiguous; use the Investment OS front door",
            "must_invoke_child_workflow": True,
            "next_action": "load_front_door_then_clarify",
            "routing_receipt": "ROUTE=unknown; CHILD=investment-os-review; NEXT_ACTION=load_front_door_then_clarify",
        }

    return {
        "is_investment_request": True,
        "route": route,
        "child_workflow": child,
        "reason": reason,
        "must_invoke_child_workflow": True,
        "routing_receipt": f"ROUTE={route}; CHILD={child}; NEXT_ACTION=load_skill({child})",
    }


if __name__ == "__main__":
    mcp.run()
