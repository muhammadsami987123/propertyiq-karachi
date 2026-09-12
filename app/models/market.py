"""Internal domain models for market data and trend points."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.models.enums import Confidence, DataType, PropertyType, TransactionType


class MarketRecord(BaseModel):
    """A single market-data record as stored in karachi_market_data.json."""

    model_config = ConfigDict(extra="allow")

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


class TrendPoint(BaseModel):
    """A single trend observation as stored in karachi_market_trends.json."""

    model_config = ConfigDict(extra="allow")

    location_id: str
    property_type: PropertyType
    transaction_type: TransactionType
    metric: str
    period: str
    value: float
    data_type: DataType
