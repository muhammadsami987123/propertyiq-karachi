"""Internal domain model for a Karachi locality."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MarketCategory


class Location(BaseModel):
    """A locality record as stored in karachi_locations.json."""

    model_config = ConfigDict(extra="allow")

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
