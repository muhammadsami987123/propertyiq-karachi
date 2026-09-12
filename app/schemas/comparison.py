"""API schemas for the multi-location comparison endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class ComparisonMetric(BaseModel):
    location_id: str
    name: str
    sale_price_min: float | None = None
    sale_price_max: float | None = None
    sale_price_avg: float | None = None
    rent_price_min: float | None = None
    rent_price_max: float | None = None
    rent_price_avg: float | None = None
    price_per_sqft_avg: float | None = None
    gross_rental_yield_pct: float | None = None
    yield_unavailable_reason: str | None = None
    trend_pct: float | None = None
    trend_unavailable_reason: str | None = None
    confidence: str | None = None


class ComparisonResponse(BaseModel):
    requested_ids: list[str]
    not_found_ids: list[str]
    results: list[ComparisonMetric]
