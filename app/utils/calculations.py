"""Pure, unit-testable investment-calculator math. No I/O in this module.

Formula notes
-------------
- ``monthly_payment`` is the standard amortized mortgage payment on the
  financed principal (purchase_price - down_payment). When the annual
  interest rate is 0%, we fall back to straight-line division of principal
  over the number of months (no interest accrues).
- ``net_rental_income`` deliberately EXCLUDES the mortgage payment. It
  represents the property's own operating profit (rent minus maintenance
  and taxes/fees only), which is the conventional basis for "net yield" in
  real-estate analysis. The mortgage is a financing choice, not an
  operating expense of the property itself.
- ``annual_expenses`` (used for cash-on-cash return and breakeven) DOES
  include the mortgage payment, because those two metrics answer "how much
  cash am I putting in vs. getting out of my pocket", which must account
  for debt service.
"""

from __future__ import annotations

from dataclasses import dataclass


def monthly_mortgage_payment(
    principal: float, annual_interest_rate_pct: float, loan_term_years: float
) -> float:
    """Standard amortized monthly payment.

    Handles the 0% interest edge case as straight-line division of
    principal over the number of months.
    """
    n_months = loan_term_years * 12
    if n_months <= 0:
        return 0.0
    if principal <= 0:
        return 0.0

    monthly_rate = (annual_interest_rate_pct / 100.0) / 12.0
    if monthly_rate == 0:
        return principal / n_months

    factor = (1 + monthly_rate) ** n_months
    return principal * (monthly_rate * factor) / (factor - 1)


@dataclass
class CalculatorResult:
    monthly_payment: float
    annual_rental_income: float
    annual_expenses: float
    net_rental_income: float
    gross_yield_pct: float
    net_yield_pct: float
    cash_on_cash_return_pct: float | None
    breakeven_years: float | None
    estimated_total_cost: float


def run_investment_calculator(
    *,
    purchase_price: float,
    down_payment: float,
    interest_rate_pct: float,
    loan_term_years: float,
    monthly_rent: float,
    monthly_maintenance: float,
    annual_taxes_fees: float,
    vacancy_rate_pct: float,
) -> CalculatorResult:
    """Compute all investment-calculator metrics from validated inputs."""

    principal = max(purchase_price - down_payment, 0.0)
    monthly_payment = monthly_mortgage_payment(
        principal, interest_rate_pct, loan_term_years
    )

    annual_rental_income = monthly_rent * 12 * (1 - vacancy_rate_pct / 100.0)
    operating_costs = monthly_maintenance * 12 + annual_taxes_fees
    annual_expenses = operating_costs + (monthly_payment * 12)

    net_rental_income = annual_rental_income - operating_costs

    gross_yield_pct = (
        (monthly_rent * 12 / purchase_price) * 100 if purchase_price > 0 else 0.0
    )
    net_yield_pct = (
        (net_rental_income / purchase_price) * 100 if purchase_price > 0 else 0.0
    )

    net_cash_flow = annual_rental_income - annual_expenses

    cash_on_cash_return_pct: float | None
    if down_payment > 0:
        cash_on_cash_return_pct = (net_cash_flow / down_payment) * 100
    else:
        cash_on_cash_return_pct = None

    breakeven_years: float | None
    if net_cash_flow > 0 and down_payment > 0:
        breakeven_years = down_payment / net_cash_flow
    else:
        breakeven_years = None

    estimated_total_cost = purchase_price + annual_taxes_fees

    return CalculatorResult(
        monthly_payment=monthly_payment,
        annual_rental_income=annual_rental_income,
        annual_expenses=annual_expenses,
        net_rental_income=net_rental_income,
        gross_yield_pct=gross_yield_pct,
        net_yield_pct=net_yield_pct,
        cash_on_cash_return_pct=cash_on_cash_return_pct,
        breakeven_years=breakeven_years,
        estimated_total_cost=estimated_total_cost,
    )


def pct_change(old_value: float, new_value: float) -> float | None:
    """Percentage change from old_value to new_value, or None if undefined."""
    if old_value == 0:
        return None
    return ((new_value - old_value) / abs(old_value)) * 100


def gross_rental_yield_pct(sale_price_avg: float, monthly_rent_avg: float) -> float | None:
    """Gross annual rental yield %, given comparable sale and monthly-rent averages."""
    if sale_price_avg <= 0:
        return None
    return (monthly_rent_avg * 12 / sale_price_avg) * 100
