"""API schemas for location endpoints."""

from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import MarketCategory


class LocationSummary(BaseModel):
    id: str
    name: str
    slug: str
    town: str | None = None
    latitude: float
    longitude: float
    market_category: MarketCategory


class NearbyLocation(BaseModel):
    id: str
    name: str
    slug: str


class LocationDetail(BaseModel):
    id: str
    slug: str
    name: str
    city: str
    town: str | None = None
    latitude: float
    longitude: float
    market_category: MarketCategory
    description: str | None = None
    nearby_locations: list[NearbyLocation]
    data_freshness: str | None = None
