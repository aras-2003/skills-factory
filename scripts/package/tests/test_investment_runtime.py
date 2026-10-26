from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "runtime" / "mcp" / "investment_runtime.py"


def load_runtime():
    spec = importlib.util.spec_from_file_location("skills_factory_investment_runtime", RUNTIME)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load investment runtime")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InvestmentRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = load_runtime()

    def assert_route(self, prompt: str, route: str, child: str) -> None:
        result = self.runtime.route_investment_request(prompt)
        self.assertTrue(result["is_investment_request"])
        self.assertEqual(route, result["route"])
        self.assertEqual(child, result["child_workflow"])
        self.assertTrue(result["must_invoke_child_workflow"])
        self.assertEqual(
            f"ROUTE={route}; CHILD={child}; NEXT_ACTION=load_skill({child})",
            result["routing_receipt"],
        )

    def test_server_instructions_require_pre_analysis_routing(self) -> None:
        instructions = self.runtime.SERVER_INSTRUCTIONS
        self.assertIn("Before substantive investment analysis", instructions)
        self.assertIn("route_investment_request", instructions)
        self.assertIn("investment-portfolio-review", instructions)
        self.assertIn("auditable front-door routing receipt", instructions)
        self.assertIn("Do not silently substitute another specialist", instructions)
        self.assertIn("Do not replace", instructions)

    def test_routes_portfolio_weights(self) -> None:
        self.assert_route(
            "Review this portfolio: ACN 25.26%, IUIT 22.16%, SMH 5.68%. What requires attention?",
            "portfolio",
            "investment-portfolio-review",
        )

    def test_routes_single_security(self) -> None:
        self.assert_route(
            "Review MU end to end: thesis, valuation, downside and portfolio fit.",
            "security",
            "investment-security-review",
        )

    def test_review_investment_portfolio_selects_portfolio_child(self) -> None:
        for prompt in (
            "Review my investment portfolio.",
            "Review this investment portfolio.",
            "Review the investment portfolio.",
            "Review my investment portfolio; routing only, do not read data or execute a child workflow.",
        ):
            with self.subTest(prompt=prompt):
                self.assert_route(prompt, "portfolio", "investment-portfolio-review")

    def test_negated_investment_portfolio_review_keeps_discovery_route(self) -> None:
        self.assert_route(
            "Find new stocks worth researching; do not review my investment portfolio.",
            "opportunity",
            "investment-opportunity-hunter",
        )

    def test_ambiguous_share_ownership_requests_front_door_clarification(self) -> None:
        for prompt in (
            "Mam akcje. Co zrobić?",
            "Mam akcje kilku spółek. Co powinienem z nimi zrobić?",
            "I own some shares. What should I do?",
        ):
            with self.subTest(prompt=prompt):
                result = self.runtime.route_investment_request(prompt)
                self.assertTrue(result["is_investment_request"])
                self.assertEqual("unknown", result["route"])
                self.assertEqual("investment-os-review", result["child_workflow"])
                self.assertIn("ambiguous", result["reason"])
                self.assertTrue(result["must_invoke_child_workflow"])
                self.assertEqual("load_front_door_then_clarify", result["next_action"])
                self.assertEqual(
                    "ROUTE=unknown; CHILD=investment-os-review; NEXT_ACTION=load_front_door_then_clarify",
                    result["routing_receipt"],
                )

    def test_direct_stock_review_still_routes(self) -> None:
        self.assert_route("Review stock ACN", "security", "investment-security-review")

    def test_routes_opportunity_discovery(self) -> None:
        self.assert_route(
            "Chcę znaleźć kilka nowych spółek dostępnych przez mojego brokera, które warto teraz dalej zbadać. Nie mam jeszcze konkretnego tickera. Zrób selekcję kandydatów do researchu, a nie analizę mojego obecnego portfela.",
            "opportunity",
            "investment-opportunity-hunter",
        )

    def test_negative_portfolio_mention_does_not_override_opportunity_discovery(self) -> None:
        self.assert_route(
            "Find a few new stocks worth researching, not a review of my current portfolio.",
            "opportunity",
            "investment-opportunity-hunter",
        )

    def test_positive_holdings_request_survives_negative_portfolio_comparison(self) -> None:
        self.assert_route(
            "Review these holdings and weights, not a generic portfolio overview: ACN 25%, IUIT 20%.",
            "portfolio",
            "investment-portfolio-review",
        )

    def test_routes_theme_research(self) -> None:
        self.assert_route(
            "Research investment themes around AI infrastructure and second-order beneficiaries.",
            "theme",
            "investment-theme-discovery",
        )

    def test_exact_natural_routing_regressions(self) -> None:
        cases = {
            "portfolio-natural-en": ("portfolio", "investment-portfolio-review"),
            "portfolio-observation-natural-pl": ("portfolio_observation", "investment-portfolio-observation"),
            "security-natural-en": ("security", "investment-security-review"),
            "security-sizing-natural-en": ("security", "investment-security-review"),
            "opportunity-natural-pl": ("opportunity", "investment-opportunity-hunter"),
            "theme-natural-en": ("theme", "investment-theme-discovery"),
            "attention-natural-pl": ("attention", "investment-attention-review"),
            "policy-natural-pl": ("policy", "investment-policy-design"),
        }
        for case, (route, child) in cases.items():
            with self.subTest(case=case):
                prompt = (ROOT / "evals/routing" / f"investment-{case}.input.md").read_text()
                self.assert_route(prompt, route, child)

    def test_routes_attention_triage(self) -> None:
        self.assert_route(
            "Pojawiły się nowe informacje o mojej spółce. Czy to zmienia tezę inwestycyjną?",
            "attention",
            "investment-attention-review",
        )

    def test_watchlist_earnings_information_routes_to_attention(self) -> None:
        for prompt in (
            "A company in my watchlist just reported earnings. Triage whether it changes my thesis and what deserves deeper research.",
            "Spółka z mojej watchlisty opublikowała nowe wyniki. Oceń ich wpływ na tezę i powiedz, co wymaga dalszej analizy.",
        ):
            with self.subTest(prompt=prompt):
                self.assert_route(prompt, "attention", "investment-attention-review")

    def test_named_holding_earnings_attention_routes_to_attention_in_both_languages(self) -> None:
        for prompt in (
            "Review the latest earnings event for my holding, ticker NVDA, and tell me if it warrants thesis attention.",
            "Przejrzyj ostatnie wyniki spółki z mojego portfela, ticker NVDA, i powiedz, czy wymagają uwagi dla tezy.",
        ):
            with self.subTest(prompt=prompt):
                self.assert_route(prompt, "attention", "investment-attention-review")

    def test_earnings_thesis_change_routes_to_attention_without_explicit_attention_word(self) -> None:
        for prompt in (
            "AAPL reported quarterly earnings today. Review whether the result changes my existing investment thesis. Do not analyze beyond routing.",
            "AAPL opublikował dziś wyniki kwartalne. Sprawdź, czy wynik zmienia moją istniejącą tezę inwestycyjną. Nie analizuj poza routingiem.",
        ):
            with self.subTest(prompt=prompt):
                self.assert_route(prompt, "attention", "investment-attention-review")

    def test_user_reported_earnings_thesis_wording_routes_in_both_languages(self) -> None:
        for prompt in (
            "For my portfolio holding, explain how its latest earnings event changes my existing investment thesis.",
            "Dla spółki z mojego portfela wyjaśnij, jak najnowszy raport wynikowy zmienia moją dotychczasową tezę inwestycyjną.",
        ):
            with self.subTest(prompt=prompt):
                self.assert_route(prompt, "attention", "investment-attention-review")

    def test_sector_opportunity_discovery_routes_in_both_languages(self) -> None:
        for prompt in (
            "Find promising opportunities in the renewable energy sector; I want a new company to research.",
            "Znajdź obiecujące okazje w sektorze energii odnawialnej; chcę nową spółkę do analizy.",
        ):
            with self.subTest(prompt=prompt):
                self.assert_route(prompt, "opportunity", "investment-opportunity-hunter")

    def test_routes_policy_design(self) -> None:
        self.assert_route(
            "Pomóż mi ustalić zasady portfela: maksymalny udział jednej spółki i limity sektorowe.",
            "policy",
            "investment-policy-design",
        )

    def test_empty_request_does_not_force_child(self) -> None:
        result = self.runtime.route_investment_request("   ")
        self.assertFalse(result["is_investment_request"])
        self.assertFalse(result["must_invoke_child_workflow"])

    def test_unrelated_governance_security_and_sentinel_prompts_are_not_routed(self) -> None:
        for prompt in (
            "The archived BACKLOG.json says tasks are proposed, while Issues and Project show active work.",
            "A public repository has no confirmed LICENSE and private vulnerability reporting is not verified.",
            "Repo source CI is green, but reading branch protection /rules yields HTTP 403.",
            "A scanner passes a source fixture but no model/runtime tool trace exists.",
            "Fix punctuation only: 'Zespół, pracuje sprawnie'. No finance, process, organization or investments analysis.",
            "A synthetic DTC order is 123 PLN gross at 23% VAT. State its net revenue.",
        ):
            with self.subTest(prompt=prompt):
                result = self.runtime.route_investment_request(prompt)
                self.assertFalse(result["is_investment_request"])
                self.assertFalse(result["must_invoke_child_workflow"])
                self.assertEqual("not_applicable", result["route"])

    def test_routes_synthetic_thesis_attention_and_preview_watchlist(self) -> None:
        self.assert_route(
            "Synthetic thesis fixture: status ACTIVE, required gross margin >=20%, unverified report suggests 15%; give attention next research.",
            "attention",
            "investment-attention-review",
        )
        self.assert_route(
            "Synthetic investing request: give a preview-only watchlist screen. Do not persist research history.",
            "opportunity",
            "investment-opportunity-hunter",
        )

    def test_candidate_screen_is_not_misrouted_by_incidental_xtb_history(self) -> None:
        self.assert_route(
            "Synthetic investing request: Candidate TESTCO-A has two synthetic confirmed contracts and a growing synthetic backlog; "
            "margins, valuation and XTB history are UNKNOWN. Preview the screen and preserve uncertainty.",
            "opportunity",
            "investment-opportunity-hunter",
        )


if __name__ == "__main__":
    unittest.main()
