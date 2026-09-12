import pytest

from app.utils.calculations import (
    gross_rental_yield_pct,
    monthly_mortgage_payment,
    pct_change,
    run_investment_calculator,
)


def test_monthly_mortgage_payment_zero_interest():
    payment = monthly_mortgage_payment(1_200_000, 0, 10)
    assert payment == pytest.approx(10_000, rel=1e-6)


def test_monthly_mortgage_payment_positive_interest():
    payment = monthly_mortgage_payment(16_000_000, 15, 20)
    assert payment > 0
    # Amortized payment must exceed the straight-line (no-interest) equivalent.
    assert payment > 16_000_000 / (20 * 12)


def test_monthly_mortgage_payment_zero_principal():
    assert monthly_mortgage_payment(0, 15, 20) == 0.0


def test_run_investment_calculator_basic():
    result = run_investment_calculator(
        purchase_price=20_000_000,
        down_payment=4_000_000,
        interest_rate_pct=15,
        loan_term_years=20,
        monthly_rent=90_000,
        monthly_maintenance=5_000,
        annual_taxes_fees=50_000,
        vacancy_rate_pct=5,
    )
    assert result.monthly_payment > 0
    assert result.annual_rental_income == pytest.approx(90_000 * 12 * 0.95)
    assert result.net_rental_income < result.annual_rental_income
    assert result.gross_yield_pct == pytest.approx((90_000 * 12 / 20_000_000) * 100)
    assert result.estimated_total_cost == pytest.approx(20_050_000)


def test_run_investment_calculator_zero_down_payment_has_no_cash_on_cash():
    result = run_investment_calculator(
        purchase_price=10_000_000,
        down_payment=0,
        interest_rate_pct=10,
        loan_term_years=15,
        monthly_rent=50_000,
        monthly_maintenance=2_000,
        annual_taxes_fees=10_000,
        vacancy_rate_pct=0,
    )
    assert result.cash_on_cash_return_pct is None
    assert result.breakeven_years is None


def test_pct_change():
    assert pct_change(100, 110) == pytest.approx(10.0)
    assert pct_change(0, 50) is None


def test_gross_rental_yield_pct():
    assert gross_rental_yield_pct(12_000_000, 60_000) == pytest.approx((60_000 * 12 / 12_000_000) * 100)
    assert gross_rental_yield_pct(0, 60_000) is None
