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


if __name__ == "__main__":
    unittest.main()
