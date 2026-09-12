"""API schemas for admin endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import Confidence, DataType, MarketCategory, PropertyType, TransactionType


class SourceOut(BaseModel):
    id: str
    name: str
    url: str | None = None
    type: str
    description: str | None = None
    terms_note: str | None = None


class LocationUpsertRequest(BaseModel):
    id: str
    slug: str
    name: str
    city: str = "Karachi"
    town: str | None = None
    latitude: float
    longitude: float
    market_category: MarketCategory
    description: str | None = None
    nearby_ids: list[str] = Field(default_factory=list)


class MarketRecordUpsertRequest(BaseModel):
    id: str
    location_id: str
    property_type: PropertyType
    transaction_type: TransactionType
    price_min: float
    price_max: float
    price_avg: float
    price_per_sqft_min: float | None = None
    price_per_sqft_max: float | None = None
    currency: str = "PKR"
    data_type: DataType
    source: str | None = None
    source_url: str | None = None
    collected_at: str | None = None
    last_updated: str | None = None
    confidence: Confidence
    observations: int | None = None
    methodology: str | None = None
    notes: str | None = None


class ImportRowError(BaseModel):
    row: int
    message: str


class ImportResult(BaseModel):
    imported: int
    errors: list[ImportRowError]
