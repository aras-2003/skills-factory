"""Regression coverage for business lifecycle classification."""
import importlib.util
from pathlib import Path
import pytest

SCRIPT = (Path(__file__).resolve().parents[2] / "skills/investing/security-underwriting"
          / "scripts/business_lifecycle.py")
spec = importlib.util.spec_from_file_location("business_lifecycle", SCRIPT)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)
FinancialPeriod = module.FinancialPeriod
classify = module.classify_lifecycle


def test_missing_history_is_not_classified():
    assert classify([FinancialPeriod("2025", 100, 20)])["status"] == "INSUFFICIENT_DATA"


def test_operating_leverage_on_margin_expansion():
    result = classify([FinancialPeriod("2023", 100, 5), FinancialPeriod("2024", 120, 8),
                       FinancialPeriod("2025", 145, 22, 18, 0)])
    assert result["phase"] == "operating_leverage"
    assert result["probabilities_calibrated"] is False


def test_capital_returns_for_mature_cash_generative_business():
    result = classify([FinancialPeriod("2023", 100, 25, 22, 15),
                       FinancialPeriod("2024", 104, 26, 23, 16),
                       FinancialPeriod("2025", 107, 27, 25, 18)])
    assert result["phase"] == "capital_return"


def test_decline_requires_persistent_contraction():
    result = classify([FinancialPeriod("2023", 120, 25), FinancialPeriod("2024", 100, 17),
                       FinancialPeriod("2025", 80, 8)])
    assert result["phase"] == "decline"


def test_loss_making_fast_growth():
    result = classify([FinancialPeriod("2023", 60, -20), FinancialPeriod("2024", 90, -18),
                       FinancialPeriod("2025", 135, -8)])
    assert result["phase"] == "hyper_growth"


def test_nonfinite_and_duplicate_periods_rejected():
    with pytest.raises(ValueError):
        FinancialPeriod("2025", float("nan"), 5)
    with pytest.raises(ValueError):
        classify([FinancialPeriod("2023", 10, 1), FinancialPeriod("2023", 11, 1),
                  FinancialPeriod("2025", 12, 2)])
