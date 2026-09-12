"""Heatmap analytics endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.models.enums import PropertyType, TransactionType
from app.schemas.analytics import HeatmapResponse
from app.services.market import compute_heatmap

router = APIRouter(tags=["analytics"])

VALID_METRICS = {"price_per_sqft", "price", "rent", "growth", "yield"}


@router.get("/analytics/heatmap", response_model=HeatmapResponse)
def heatmap(
    metric: str = Query(...),
    transaction_type: TransactionType = Query(...),
    property_type: PropertyType | None = Query(default=None),
) -> dict:
    if metric not in VALID_METRICS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric '{metric}'. Must be one of: {sorted(VALID_METRICS)}",
        )

    result = compute_heatmap(
        metric=metric,
        transaction_type=transaction_type.value,
        property_type=property_type.value if property_type else None,
    )

    return {
        "metric": metric,
        "transaction_type": transaction_type.value,
        "property_type": property_type.value if property_type else None,
        "items": result["items"],
        "legend": result["legend"],
    }
