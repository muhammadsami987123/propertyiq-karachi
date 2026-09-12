"""Multi-location comparison endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.comparison import ComparisonResponse
from app.services.market import compute_comparison

router = APIRouter(tags=["comparison"])


@router.get("/comparison", response_model=ComparisonResponse)
def comparison(ids: str = Query(..., description="Comma-separated location ids (2-4)")) -> dict:
    id_list = [i.strip() for i in ids.split(",") if i.strip()]

    if len(id_list) < 2 or len(id_list) > 4:
        raise HTTPException(
            status_code=400,
            detail="Please provide between 2 and 4 location ids to compare.",
        )

    result = compute_comparison(id_list)

    if result["not_found_ids"] and not result["results"]:
        raise HTTPException(
            status_code=400,
            detail=f"None of the requested location ids were found: {result['not_found_ids']}",
        )

    return result
