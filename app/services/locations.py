"""Business logic for location listing, detail, and market lookups."""

from __future__ import annotations

from typing import Any

from app.services import data_store


def get_all_locations() -> list[dict[str, Any]]:
    return data_store.load_locations()


def get_location_by_id(location_id: str) -> dict[str, Any] | None:
    for loc in data_store.load_locations():
        if loc.get("id") == location_id:
            return loc
    return None


def resolve_nearby(location: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve nearby_ids to lightweight {id, name, slug} dicts."""
    all_locations = {loc.get("id"): loc for loc in data_store.load_locations()}
    resolved = []
    for nid in location.get("nearby_ids", []) or []:
        nearby = all_locations.get(nid)
        if nearby:
            resolved.append(
                {
                    "id": nearby.get("id"),
                    "name": nearby.get("name"),
                    "slug": nearby.get("slug"),
                }
            )
    return resolved


def get_market_records_for_location(location_id: str) -> list[dict[str, Any]]:
    return [
        r
        for r in data_store.load_market_records()
        if r.get("location_id") == location_id
    ]


def get_data_freshness(location_id: str) -> str | None:
    """Most recent last_updated among a location's market records."""
    records = get_market_records_for_location(location_id)
    dates = [r.get("last_updated") for r in records if r.get("last_updated")]
    if not dates:
        return None
    return max(dates)


def get_trends_for_location(location_id: str) -> list[dict[str, Any]]:
    return [
        t
        for t in data_store.load_trends()
        if t.get("location_id") == location_id
    ]


def build_confidence_explanation(records: list[dict[str, Any]]) -> str:
    """Human-readable explanation of confidence factors for a location's data."""
    if not records:
        return (
            "No market records are available for this locality yet, so a "
            "confidence level cannot be assessed."
        )

    total_observations = sum(r.get("observations") or 0 for r in records)
    confidences = {r.get("confidence") for r in records if r.get("confidence")}
    data_types = {r.get("data_type") for r in records if r.get("data_type")}
    freshest = max((r.get("last_updated") for r in records if r.get("last_updated")), default=None)

    confidence_summary = (
        ", ".join(sorted(confidences)) if confidences else "unspecified"
    )
    source_summary = ", ".join(sorted(data_types)) if data_types else "unspecified"

    return (
        f"Confidence level(s) present: {confidence_summary}. Based on "
        f"{total_observations} aggregate observation(s) across "
        f"{len(records)} record(s), sourced from data of type(s): "
        f"{source_summary}. Most recently updated on "
        f"{freshest or 'an unknown date'}. Confidence reflects observation "
        f"count, source quality, data freshness, geographic specificity "
        f"(locality-level vs. broader area), and consistency across "
        f"available records."
    )
