#!/usr/bin/env python3
"""
validate_data.py — Standalone data-integrity checker for PropertyIQ's
Karachi dataset (app/data/**).

Validates, without any third-party dependency:
  * every JSON/GeoJSON file under app/data/ parses cleanly
  * every record's required fields, enum values, and numeric/date invariants
  * referential integrity across locations, market data, trends, and
    localities.geojson

Usage:
    python scripts/validate_data.py [--data-dir app/data]

Exit code 0 = clean, 1 = one or more errors found.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Domain vocabulary (mirrors app/models/enums.py — kept dependency-free here
# on purpose so this script runs even without the app package importable).
# ---------------------------------------------------------------------------

PROPERTY_TYPES = {"house", "apartment", "plot", "commercial", "office", "shop"}
TRANSACTION_TYPES = {"sale", "rent"}
MARKET_CATEGORIES = {
    "premium",
    "upper-mid",
    "mid-market",
    "affordable",
    "emerging",
    "commercial",
    "mixed",
}
DATA_TYPES = {
    "verified",
    "listing_aggregate",
    "research_estimate",
    "historical",
    "calculated",
    "user_provided",
    "demo",
}
CONFIDENCE_LEVELS = {"high", "medium", "low"}

# Rough Karachi bounding box.
LAT_MIN, LAT_MAX = 24.7, 25.2
LON_MIN, LON_MAX = 66.6, 67.5


class ErrorCollector:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, file: str, ref: str, message: str) -> None:
        self.errors.append(f"[{file}] {ref}: {message}")

    def warn(self, file: str, ref: str, message: str) -> None:
        self.warnings.append(f"[{file}] {ref}: {message}")

    @property
    def ok(self) -> bool:
        return not self.errors


def load_json(path: Path, ec: ErrorCollector) -> Any | None:
    if not path.exists():
        ec.warn(str(path), "-", "file not found (skipped)")
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        ec.error(str(path), "-", f"could not read file: {exc}")
        return None
    if not text.strip():
        ec.warn(str(path), "-", "file is empty (skipped)")
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        ec.error(str(path), "-", f"invalid JSON: {exc}")
        return None


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_iso_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def require_fields(
    record: dict, fields: list[str], file: str, ref: str, ec: ErrorCollector
) -> None:
    for field in fields:
        if field not in record or record[field] is None:
            ec.error(file, ref, f"missing required field '{field}'")


# ---------------------------------------------------------------------------
# Per-file validators
# ---------------------------------------------------------------------------


def validate_locations(path: Path, ec: ErrorCollector) -> dict[str, dict]:
    """Returns a map of location_id -> location record for cross-checks."""
    data = load_json(path, ec)
    locations: dict[str, dict] = {}
    if data is None:
        return locations
    if not isinstance(data, list):
        ec.error(str(path), "-", "expected a JSON array of location objects")
        return locations

    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()
    for idx, rec in enumerate(data):
        ref = f"record #{idx} (id={rec.get('id', '?')})" if isinstance(rec, dict) else f"record #{idx}"
        if not isinstance(rec, dict):
            ec.error(str(path), ref, "record is not a JSON object")
            continue

        require_fields(
            rec,
            ["id", "slug", "name", "city", "latitude", "longitude", "market_category"],
            str(path),
            ref,
            ec,
        )

        rec_id = rec.get("id")
        if isinstance(rec_id, str):
            if rec_id in seen_ids:
                ec.error(str(path), ref, f"duplicate id '{rec_id}'")
            seen_ids.add(rec_id)
            locations[rec_id] = rec

        slug = rec.get("slug")
        if isinstance(slug, str):
            if slug in seen_slugs:
                ec.error(str(path), ref, f"duplicate slug '{slug}'")
            seen_slugs.add(slug)

        mc = rec.get("market_category")
        if mc is not None and mc not in MARKET_CATEGORIES:
            ec.error(str(path), ref, f"invalid market_category '{mc}'")

        lat = rec.get("latitude")
        lon = rec.get("longitude")
        if lat is not None:
            if not is_number(lat):
                ec.error(str(path), ref, f"latitude is not numeric: {lat!r}")
            elif not (LAT_MIN <= lat <= LAT_MAX):
                ec.error(str(path), ref, f"latitude {lat} outside Karachi bounds ({LAT_MIN}-{LAT_MAX})")
        if lon is not None:
            if not is_number(lon):
                ec.error(str(path), ref, f"longitude is not numeric: {lon!r}")
            elif not (LON_MIN <= lon <= LON_MAX):
                ec.error(str(path), ref, f"longitude {lon} outside Karachi bounds ({LON_MIN}-{LON_MAX})")

        nearby = rec.get("nearby_ids", [])
        if nearby is not None and not isinstance(nearby, list):
            ec.error(str(path), ref, "nearby_ids must be a list")

    return locations


def validate_market_data(
    path: Path, ec: ErrorCollector, location_ids: set[str]
) -> list[dict]:
    data = load_json(path, ec)
    if data is None:
        return []
    if not isinstance(data, list):
        ec.error(str(path), "-", "expected a JSON array of market records")
        return []

    seen_ids: set[str] = set()
    for idx, rec in enumerate(data):
        ref = f"record #{idx} (id={rec.get('id', '?')})" if isinstance(rec, dict) else f"record #{idx}"
        if not isinstance(rec, dict):
            ec.error(str(path), ref, "record is not a JSON object")
            continue

        require_fields(
            rec,
            [
                "id",
                "location_id",
                "property_type",
                "transaction_type",
                "price_min",
                "price_max",
                "price_avg",
                "currency",
                "data_type",
                "confidence",
            ],
            str(path),
            ref,
            ec,
        )

        rec_id = rec.get("id")
        if isinstance(rec_id, str):
            if rec_id in seen_ids:
                ec.error(str(path), ref, f"duplicate id '{rec_id}'")
            seen_ids.add(rec_id)

        loc_id = rec.get("location_id")
        if isinstance(loc_id, str) and location_ids and loc_id not in location_ids:
            ec.error(str(path), ref, f"location_id '{loc_id}' not found in karachi_locations.json")

        pt = rec.get("property_type")
        if pt is not None and pt not in PROPERTY_TYPES:
            ec.error(str(path), ref, f"invalid property_type '{pt}'")

        tt = rec.get("transaction_type")
        if tt is not None and tt not in TRANSACTION_TYPES:
            ec.error(str(path), ref, f"invalid transaction_type '{tt}'")

        dt = rec.get("data_type")
        if dt is not None and dt not in DATA_TYPES:
            ec.error(str(path), ref, f"invalid data_type '{dt}'")

        conf = rec.get("confidence")
        if conf is not None and conf not in CONFIDENCE_LEVELS:
            ec.error(str(path), ref, f"invalid confidence '{conf}'")

        currency = rec.get("currency")
        if currency is not None and currency != "PKR":
            ec.error(str(path), ref, f"currency must be 'PKR', got '{currency}'")

        price_min = rec.get("price_min")
        price_max = rec.get("price_max")
        price_avg = rec.get("price_avg")
        for field_name, value in (
            ("price_min", price_min),
            ("price_max", price_max),
            ("price_avg", price_avg),
        ):
            if value is not None:
                if not is_number(value):
                    ec.error(str(path), ref, f"{field_name} is not numeric: {value!r}")
                elif value < 0:
                    ec.error(str(path), ref, f"{field_name} must be non-negative, got {value}")

        if all(is_number(v) for v in (price_min, price_max, price_avg) if v is not None) and None not in (
            price_min,
            price_max,
            price_avg,
        ):
            if not (price_min <= price_avg <= price_max):
                ec.error(
                    str(path),
                    ref,
                    f"expected price_min <= price_avg <= price_max, got "
                    f"{price_min} <= {price_avg} <= {price_max}",
                )

        sqft_min = rec.get("price_per_sqft_min")
        sqft_max = rec.get("price_per_sqft_max")
        for field_name, value in (("price_per_sqft_min", sqft_min), ("price_per_sqft_max", sqft_max)):
            if value is not None:
                if not is_number(value):
                    ec.error(str(path), ref, f"{field_name} is not numeric: {value!r}")
                elif value < 0:
                    ec.error(str(path), ref, f"{field_name} must be non-negative, got {value}")
        if is_number(sqft_min) and is_number(sqft_max) and sqft_min > sqft_max:
            ec.error(
                str(path),
                ref,
                f"expected price_per_sqft_min <= price_per_sqft_max, got {sqft_min} > {sqft_max}",
            )

        observations = rec.get("observations")
        if observations is not None:
            if not is_number(observations) or observations < 0:
                ec.error(str(path), ref, f"observations must be a non-negative number, got {observations!r}")

        for date_field in ("collected_at", "last_updated"):
            value = rec.get(date_field)
            if value is not None and not is_iso_date(value):
                ec.error(str(path), ref, f"{date_field} is not a valid ISO date string: {value!r}")

    return data if isinstance(data, list) else []


def validate_trends(path: Path, ec: ErrorCollector, location_ids: set[str]) -> None:
    data = load_json(path, ec)
    if data is None:
        return
    if not isinstance(data, list):
        ec.error(str(path), "-", "expected a JSON array of trend records")
        return

    for idx, rec in enumerate(data):
        ref = f"record #{idx}"
        if not isinstance(rec, dict):
            ec.error(str(path), ref, "record is not a JSON object")
            continue

        require_fields(
            rec,
            ["location_id", "property_type", "transaction_type", "metric", "period", "value", "data_type"],
            str(path),
            ref,
            ec,
        )

        loc_id = rec.get("location_id")
        if isinstance(loc_id, str) and location_ids and loc_id not in location_ids:
            ec.error(str(path), ref, f"location_id '{loc_id}' not found in karachi_locations.json")

        pt = rec.get("property_type")
        if pt is not None and pt not in PROPERTY_TYPES:
            ec.error(str(path), ref, f"invalid property_type '{pt}'")

        tt = rec.get("transaction_type")
        if tt is not None and tt not in TRANSACTION_TYPES:
            ec.error(str(path), ref, f"invalid transaction_type '{tt}'")

        dt = rec.get("data_type")
        if dt is not None and dt not in DATA_TYPES:
            ec.error(str(path), ref, f"invalid data_type '{dt}'")

        value = rec.get("value")
        if value is not None and not is_number(value):
            ec.error(str(path), ref, f"value is not numeric: {value!r}")


def validate_sources(path: Path, ec: ErrorCollector) -> None:
    data = load_json(path, ec)
    if data is None:
        return
    if not isinstance(data, list):
        ec.error(str(path), "-", "expected a JSON array of source objects")
        return

    seen_ids: set[str] = set()
    for idx, rec in enumerate(data):
        ref = f"record #{idx}"
        if not isinstance(rec, dict):
            ec.error(str(path), ref, "record is not a JSON object")
            continue
        require_fields(rec, ["id", "name", "type"], str(path), ref, ec)
        if "url" not in rec:
            ec.error(str(path), ref, "missing required field 'url'")
        elif rec["url"] is not None and not isinstance(rec["url"], str):
            ec.error(str(path), ref, "field 'url' must be a string or null")
        rec_id = rec.get("id")
        if isinstance(rec_id, str):
            if rec_id in seen_ids:
                ec.error(str(path), ref, f"duplicate id '{rec_id}'")
            seen_ids.add(rec_id)


def validate_geojson_generic(path: Path, ec: ErrorCollector) -> Any | None:
    data = load_json(path, ec)
    if data is None:
        return None
    if not isinstance(data, dict):
        ec.error(str(path), "-", "GeoJSON root must be a JSON object")
        return None
    gtype = data.get("type")
    if gtype not in ("Feature", "FeatureCollection"):
        ec.error(str(path), "-", f"expected GeoJSON type 'Feature' or 'FeatureCollection', got {gtype!r}")
        return None
    if gtype == "FeatureCollection":
        features = data.get("features")
        if not isinstance(features, list):
            ec.error(str(path), "-", "FeatureCollection.features must be a list")
            return None
        for idx, feature in enumerate(features):
            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                ec.error(str(path), f"feature #{idx}", "expected a GeoJSON Feature object")
                continue
            if "geometry" not in feature:
                ec.error(str(path), f"feature #{idx}", "missing 'geometry'")
    else:
        if "geometry" not in data:
            ec.error(str(path), "-", "missing 'geometry'")
    return data


def validate_localities_geojson(path: Path, ec: ErrorCollector, location_ids: set[str]) -> int:
    data = validate_geojson_generic(path, ec)
    if data is None:
        return 0
    features = data.get("features", []) if data.get("type") == "FeatureCollection" else [data]
    count = 0
    for idx, feature in enumerate(features):
        if not isinstance(feature, dict):
            continue
        count += 1
        props = feature.get("properties", {})
        if not isinstance(props, dict):
            ec.error(str(path), f"feature #{idx}", "properties must be an object")
            continue
        loc_id = props.get("location_id")
        if not loc_id:
            ec.error(str(path), f"feature #{idx}", "missing properties.location_id")
        elif location_ids and loc_id not in location_ids:
            ec.error(str(path), f"feature #{idx}", f"location_id '{loc_id}' not found in karachi_locations.json")
        if "name" not in props:
            ec.error(str(path), f"feature #{idx}", "missing properties.name")
        if "market_category" in props and props["market_category"] not in MARKET_CATEGORIES:
            ec.error(str(path), f"feature #{idx}", f"invalid market_category '{props['market_category']}'")
    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PropertyIQ's Karachi dataset.")
    parser.add_argument(
        "--data-dir",
        default="app/data",
        help="Path to the app/data directory (default: app/data)",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    ec = ErrorCollector()

    locations_path = data_dir / "locations" / "karachi_locations.json"
    market_path = data_dir / "market" / "karachi_market_data.json"
    trends_path = data_dir / "market" / "karachi_market_trends.json"
    sources_path = data_dir / "sources" / "sources.json"
    boundary_path = data_dir / "geo" / "karachi_boundary.geojson"
    localities_path = data_dir / "geo" / "localities.geojson"

    if not data_dir.exists():
        print(f"No data directory found at '{data_dir}'. Nothing to validate yet.")
        return 0

    print(f"Validating PropertyIQ dataset under: {data_dir}\n")

    locations = validate_locations(locations_path, ec)
    location_ids = set(locations.keys())

    # nearby_ids referential integrity (needs full location map).
    for loc_id, rec in locations.items():
        for nearby_id in rec.get("nearby_ids") or []:
            if nearby_id not in location_ids:
                ec.error(
                    str(locations_path),
                    f"record (id={loc_id})",
                    f"nearby_ids references unknown location_id '{nearby_id}'",
                )

    market_records = validate_market_data(market_path, ec, location_ids)
    validate_trends(trends_path, ec, location_ids)
    validate_sources(sources_path, ec)
    validate_geojson_generic(boundary_path, ec)
    feature_count = validate_localities_geojson(localities_path, ec, location_ids)

    if localities_path.exists() and locations and feature_count != len(locations):
        ec.warn(
            str(localities_path),
            "-",
            f"feature count ({feature_count}) does not match location count ({len(locations)})",
        )

    # ---- report ----
    print(f"Locations loaded:      {len(locations)}")
    print(f"Market records loaded: {len(market_records)}")
    print()

    if ec.warnings:
        print(f"Warnings ({len(ec.warnings)}):")
        for w in ec.warnings:
            print(f"  WARN  {w}")
        print()

    if ec.errors:
        print(f"Errors ({len(ec.errors)}):")
        for e in ec.errors:
            print(f"  FAIL  {e}")
        print(f"\nValidation FAILED with {len(ec.errors)} error(s).")
        return 1

    print("Validation PASSED. No errors found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
