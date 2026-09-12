"""API schemas for analytics/heatmap endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class HeatmapItem(BaseModel):
    location_id: str
    value: float | None
    confidence: str | None = None


class HeatmapLegend(BaseModel):
    min: float | None
    max: float | None


class HeatmapResponse(BaseModel):
    metric: str
    transaction_type: str
    property_type: str | None = None
    items: list[HeatmapItem]
    legend: HeatmapLegend
