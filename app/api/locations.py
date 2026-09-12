"""Location listing, detail, and market-data endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.location import LocationDetail, LocationSummary, NearbyLocation
from app.schemas.market import LocationMarketResponse, MarketRecordOut, TrendPointOut
from app.services import locations as locations_service

router = APIRouter(tags=["locations"])

NOT_FOUND_MESSAGE = "Market data is currently unavailable for this locality."


@router.get("/locations", response_model=list[LocationSummary])
def list_locations() -> list[dict]:
    return locations_service.get_all_locations()


@router.get("/locations/{location_id}", response_model=LocationDetail)
def get_location(location_id: str) -> dict:
    location = locations_service.get_location_by_id(location_id)
    if location is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)

    nearby = locations_service.resolve_nearby(location)
    freshness = locations_service.get_data_freshness(location_id)

    return {
        **location,
        "nearby_locations": [NearbyLocation(**n) for n in nearby],
        "data_freshness": freshness,
    }


@router.get("/locations/{location_id}/market", response_model=LocationMarketResponse)
def get_location_market(location_id: str) -> dict:
    location = locations_service.get_location_by_id(location_id)
    if location is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)

    records = locations_service.get_market_records_for_location(location_id)
    sale = [r for r in records if r.get("transaction_type") == "sale"]
    rent = [r for r in records if r.get("transaction_type") == "rent"]
    trends = locations_service.get_trends_for_location(location_id)
    explanation = locations_service.build_confidence_explanation(records)

    return {
        "location_id": location_id,
        "sale": [MarketRecordOut(**r) for r in sale],
        "rent": [MarketRecordOut(**r) for r in rent],
        "trends": [TrendPointOut(**t) for t in trends],
        "confidence_explanation": explanation,
    }
