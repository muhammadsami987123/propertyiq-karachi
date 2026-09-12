"""Business logic for market lookups, comparison, and heatmap analytics."""

from __future__ import annotations

from typing import Any

from app.services import data_store
from app.utils.calculations import gross_rental_yield_pct, pct_change

_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


def _worst_confidence(records: list[dict[str, Any]]) -> str | None:
    """Most conservative (lowest) confidence among records, if any."""
    ranks = [
        _CONFIDENCE_RANK[r["confidence"]]
        for r in records
        if r.get("confidence") in _CONFIDENCE_RANK
    ]
    if not ranks:
        return None
    worst_rank = min(ranks)
    for name, rank in _CONFIDENCE_RANK.items():
        if rank == worst_rank:
            return name
    return None


def _avg(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    if not values:
        return None
    return sum(values) / len(values)


def get_location_market(location_id: str) -> dict[str, Any]:
    records = [
        r for r in data_store.load_market_records() if r.get("location_id") == location_id
    ]
    sale = [r for r in records if r.get("transaction_type") == "sale"]
    rent = [r for r in records if r.get("transaction_type") == "rent"]
    trends = [
        t for t in data_store.load_trends() if t.get("location_id") == location_id
    ]
    return {"sale": sale, "rent": rent, "trends": trends}


def _trend_pct_for_location(
    location_id: str,
    property_type: str | None = None,
    transaction_type: str | None = None,
) -> float | None:
    trends = [t for t in data_store.load_trends() if t.get("location_id") == location_id]
    if property_type:
        trends = [t for t in trends if t.get("property_type") == property_type]
    if transaction_type:
        trends = [t for t in trends if t.get("transaction_type") == transaction_type]
    if not trends:
        return None

    # Group by (property_type, transaction_type, metric); use the group with
    # the most data points (most reliable trend line).
    groups: dict[tuple, list[dict[str, Any]]] = {}
    for t in trends:
        key = (t.get("property_type"), t.get("transaction_type"), t.get("metric"))
        groups.setdefault(key, []).append(t)

    best_group = max(groups.values(), key=len)
    if len(best_group) < 2:
        return None
    best_group.sort(key=lambda t: t.get("period", ""))
    oldest, newest = best_group[0], best_group[-1]
    return pct_change(oldest["value"], newest["value"])


def compute_comparison(ids: list[str]) -> dict[str, Any]:
    all_locations = {loc.get("id"): loc for loc in data_store.load_locations()}
    found_ids = [i for i in ids if i in all_locations]
    not_found_ids = [i for i in ids if i not in all_locations]

    results = []
    for location_id in found_ids:
        location = all_locations[location_id]
        market = get_location_market(location_id)
        sale, rent = market["sale"], market["rent"]

        sale_min = _avg([r["price_min"] for r in sale]) if sale else None
        sale_max = _avg([r["price_max"] for r in sale]) if sale else None
        sale_avg = _avg([r["price_avg"] for r in sale]) if sale else None

        rent_min = _avg([r["price_min"] for r in rent]) if rent else None
        rent_max = _avg([r["price_max"] for r in rent]) if rent else None
        rent_avg = _avg([r["price_avg"] for r in rent]) if rent else None

        sqft_values = [
            (r["price_per_sqft_min"] + r["price_per_sqft_max"]) / 2
            for r in sale + rent
            if r.get("price_per_sqft_min") is not None and r.get("price_per_sqft_max") is not None
        ]
        price_per_sqft_avg = _avg(sqft_values)

        # Rental yield: only for property types present in both sale & rent.
        sale_by_type = {r["property_type"]: r["price_avg"] for r in sale}
        rent_by_type = {r["property_type"]: r["price_avg"] for r in rent}
        common_types = set(sale_by_type) & set(rent_by_type)

        yield_pct = None
        yield_reason = None
        if common_types:
            yields = [
                gross_rental_yield_pct(sale_by_type[pt], rent_by_type[pt])
                for pt in common_types
            ]
            yields = [y for y in yields if y is not None]
            yield_pct = _avg(yields)
            if yield_pct is None:
                yield_reason = "Sale price data unavailable to compute yield."
        else:
            yield_reason = (
                "No comparable sale and rent records exist for the same "
                "property type at this location."
            )

        trend_pct = _trend_pct_for_location(location_id)
        trend_reason = None if trend_pct is not None else "No trend data available for this location."

        confidence = _worst_confidence(sale + rent)

        results.append(
            {
                "location_id": location_id,
                "name": location.get("name"),
                "sale_price_min": sale_min,
                "sale_price_max": sale_max,
                "sale_price_avg": sale_avg,
                "rent_price_min": rent_min,
                "rent_price_max": rent_max,
                "rent_price_avg": rent_avg,
                "price_per_sqft_avg": price_per_sqft_avg,
                "gross_rental_yield_pct": yield_pct,
                "yield_unavailable_reason": yield_reason,
                "trend_pct": trend_pct,
                "trend_unavailable_reason": trend_reason,
                "confidence": confidence,
            }
        )

    return {
        "requested_ids": ids,
        "not_found_ids": not_found_ids,
        "results": results,
    }


def compute_heatmap(
    metric: str,
    transaction_type: str,
    property_type: str | None = None,
) -> dict[str, Any]:
    locations = data_store.load_locations()
    all_records = data_store.load_market_records()

    items: list[dict[str, Any]] = []

    for loc in locations:
        location_id = loc.get("id")
        records = [
            r for r in all_records if r.get("location_id") == location_id
        ]
        if property_type:
            type_filtered = [r for r in records if r.get("property_type") == property_type]
        else:
            type_filtered = records

        value: float | None = None
        confidence: str | None = None

        if metric in ("price", "rent"):
            subset = [r for r in type_filtered if r.get("transaction_type") == transaction_type]
            if subset:
                value = _avg([r["price_avg"] for r in subset])
                confidence = _worst_confidence(subset)

        elif metric == "price_per_sqft":
            subset = [r for r in type_filtered if r.get("transaction_type") == transaction_type]
            sqft_values = [
                (r["price_per_sqft_min"] + r["price_per_sqft_max"]) / 2
                for r in subset
                if r.get("price_per_sqft_min") is not None and r.get("price_per_sqft_max") is not None
            ]
            if sqft_values:
                value = _avg(sqft_values)
                confidence = _worst_confidence(subset)

        elif metric == "growth":
            value = _trend_pct_for_location(
                location_id, property_type=property_type, transaction_type=transaction_type
            )
            if value is not None:
                confidence = _worst_confidence(type_filtered)

        elif metric == "yield":
            sale_records = [r for r in type_filtered if r.get("transaction_type") == "sale"]
            rent_records = [r for r in type_filtered if r.get("transaction_type") == "rent"]
            sale_by_type = {r["property_type"]: r["price_avg"] for r in sale_records}
            rent_by_type = {r["property_type"]: r["price_avg"] for r in rent_records}
            common_types = set(sale_by_type) & set(rent_by_type)
            if common_types:
                yields = [
                    gross_rental_yield_pct(sale_by_type[pt], rent_by_type[pt])
                    for pt in common_types
                ]
                yields = [y for y in yields if y is not None]
                if yields:
                    value = _avg(yields)
                    confidence = _worst_confidence(sale_records + rent_records)

        if value is not None:
            items.append({"location_id": location_id, "value": value, "confidence": confidence})

    values = [item["value"] for item in items]
    legend = {
        "min": min(values) if values else None,
        "max": max(values) if values else None,
    }

    return {"items": items, "legend": legend}
