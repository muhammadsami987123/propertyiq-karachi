"""API schemas for market-data endpoints."""

from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import Confidence, DataType, PropertyType, TransactionType


class MarketRecordOut(BaseModel):
    id: str
    location_id: str
    property_type: PropertyType
    transaction_type: TransactionType
    price_min: float
    price_max: float
    price_avg: float
    price_per_sqft_min: float | None = None
    price_per_sqft_max: float | None = None
    currency: str
    data_type: DataType
    source: str | None = None
    source_url: str | None = None
    collected_at: str | None = None
    last_updated: str | None = None
    confidence: Confidence
    observations: int | None = None
    methodology: str | None = None
    notes: str | None = None


class TrendPointOut(BaseModel):
    location_id: str
    property_type: PropertyType
    transaction_type: TransactionType
    metric: str
    period: str
    value: float
    data_type: DataType


class LocationMarketResponse(BaseModel):
    location_id: str
    sale: list[MarketRecordOut]
    rent: list[MarketRecordOut]
    trends: list[TrendPointOut]
    confidence_explanation: str
