"""API schemas for the investment calculator endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class CalculatorRequest(BaseModel):
    purchase_price: float = Field(ge=0)
    down_payment: float = Field(ge=0)
    interest_rate_pct: float = Field(ge=0, le=100)
    loan_term_years: float = Field(ge=0)
    monthly_rent: float = Field(ge=0)
    monthly_maintenance: float = Field(ge=0)
    annual_taxes_fees: float = Field(ge=0)
    vacancy_rate_pct: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def check_down_payment(self) -> "CalculatorRequest":
        if self.down_payment > self.purchase_price:
            raise ValueError("down_payment cannot exceed purchase_price")
        return self


class CalculatorResponse(BaseModel):
    input: CalculatorRequest
    monthly_payment: float
    annual_rental_income: float
    annual_expenses: float
    net_rental_income: float
    gross_yield_pct: float
    net_yield_pct: float
    cash_on_cash_return_pct: float | None
    breakeven_years: float | None
    estimated_total_cost: float
