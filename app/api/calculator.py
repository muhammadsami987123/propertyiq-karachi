"""Investment calculator endpoint. Thin layer over app.utils.calculations."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.calculator import CalculatorRequest, CalculatorResponse
from app.utils.calculations import run_investment_calculator

router = APIRouter(tags=["calculator"])


@router.post("/calculator", response_model=CalculatorResponse)
def calculate(payload: CalculatorRequest) -> dict:
    result = run_investment_calculator(
        purchase_price=payload.purchase_price,
        down_payment=payload.down_payment,
        interest_rate_pct=payload.interest_rate_pct,
        loan_term_years=payload.loan_term_years,
        monthly_rent=payload.monthly_rent,
        monthly_maintenance=payload.monthly_maintenance,
        annual_taxes_fees=payload.annual_taxes_fees,
        vacancy_rate_pct=payload.vacancy_rate_pct,
    )

    return {
        "input": payload,
        "monthly_payment": result.monthly_payment,
        "annual_rental_income": result.annual_rental_income,
        "annual_expenses": result.annual_expenses,
        "net_rental_income": result.net_rental_income,
        "gross_yield_pct": result.gross_yield_pct,
        "net_yield_pct": result.net_yield_pct,
        "cash_on_cash_return_pct": result.cash_on_cash_return_pct,
        "breakeven_years": result.breakeven_years,
        "estimated_total_cost": result.estimated_total_cost,
    }
