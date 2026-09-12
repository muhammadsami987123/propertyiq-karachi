"""Validation helpers: coordinate sanity, enums, CSV rows, GeoJSON structure."""

from __future__ import annotations

from typing import Any

from app.models.enums import Confidence, DataType, PropertyType, TransactionType

# Rough bounding box for Karachi, Pakistan.
KARACHI_LAT_RANGE = (24.7, 25.2)
KARACHI_LON_RANGE = (66.6, 67.5)


def is_within_karachi_bounds(latitude: float, longitude: float) -> bool:
    """Sanity-check that a coordinate plausibly lies within Karachi."""
    lat_min, lat_max = KARACHI_LAT_RANGE
    lon_min, lon_max = KARACHI_LON_RANGE
    return lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max


def validate_property_type(value: str) -> str:
    if value not in {item.value for item in PropertyType}:
        raise ValueError(f"Invalid property_type: {value!r}")
    return value


def validate_transaction_type(value: str) -> str:
    if value not in {item.value for item in TransactionType}:
        raise ValueError(f"Invalid transaction_type: {value!r}")
    return value


def validate_confidence(value: str) -> str:
    if value not in {item.value for item in Confidence}:
        raise ValueError(f"Invalid confidence: {value!r}")
    return value


def validate_data_type(value: str) -> str:
    if value not in {item.value for item in DataType}:
        raise ValueError(f"Invalid data_type: {value!r}")
    return value


REQUIRED_MARKET_CSV_COLUMNS = (
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
)


def validate_market_csv_row(row: dict[str, Any]) -> list[str]:
    """Validate one CSV row (as a dict) for market-data import.

    Returns a list of human-readable error messages (empty if valid).
    """
    errors: list[str] = []

    for column in REQUIRED_MARKET_CSV_COLUMNS:
        if not row.get(column):
            errors.append(f"Missing required field '{column}'")

    if errors:
        return errors

    try:
        validate_property_type(row["property_type"])
    except ValueError as exc:
        errors.append(str(exc))

    try:
        validate_transaction_type(row["transaction_type"])
    except ValueError as exc:
        errors.append(str(exc))

    try:
        validate_confidence(row["confidence"])
    except ValueError as exc:
        errors.append(str(exc))

    try:
        validate_data_type(row["data_type"])
    except ValueError as exc:
        errors.append(str(exc))

    for numeric_field in ("price_min", "price_max", "price_avg"):
        try:
            float(row[numeric_field])
        except (TypeError, ValueError):
            errors.append(f"Field '{numeric_field}' must be numeric")

    return errors


def validate_geojson_structure(payload: Any) -> list[str]:
    """Structurally validate a parsed GeoJSON object.

    Returns a list of human-readable error messages (empty if valid).
    Does not execute or evaluate any content — pure structural checks.
    """
    errors: list[str] = []

    if not isinstance(payload, dict):
        return ["GeoJSON root must be a JSON object"]

    geo_type = payload.get("type")
    if geo_type not in {"FeatureCollection", "Feature", "Polygon", "MultiPolygon", "Point"}:
        errors.append(f"Unsupported or missing GeoJSON 'type': {geo_type!r}")
        return errors

    if geo_type == "FeatureCollection":
        features = payload.get("features")
        if not isinstance(features, list):
            errors.append("FeatureCollection missing a 'features' array")
        else:
            for index, feature in enumerate(features):
                errors.extend(
                    f"features[{index}]: {msg}" for msg in _validate_feature(feature)
                )
    elif geo_type == "Feature":
        errors.extend(_validate_feature(payload))
    else:
        errors.extend(_validate_geometry(payload))

    return errors


def _validate_feature(feature: Any) -> list[str]:
    if not isinstance(feature, dict):
        return ["Feature must be a JSON object"]
    if feature.get("type") != "Feature":
        return ["Feature must have type == 'Feature'"]
    geometry = feature.get("geometry")
    if geometry is None:
        return ["Feature missing 'geometry'"]
    return _validate_geometry(geometry)


_GEOMETRY_DEPTH = {"Point": 1, "LineString": 2, "Polygon": 3, "MultiPolygon": 4}


def _validate_geometry(geometry: Any) -> list[str]:
    if not isinstance(geometry, dict):
        return ["Geometry must be a JSON object"]
    geom_type = geometry.get("type")
    if geom_type is None:
        return ["Geometry missing 'type'"]
    coordinates = geometry.get("coordinates")
    if coordinates is None:
        return ["Geometry missing 'coordinates'"]

    expected_depth = _GEOMETRY_DEPTH.get(geom_type)
    if expected_depth is None:
        return []  # Unrecognized/unsupported geometry type: no further shape checks.

    depth = _coordinate_nesting_depth(coordinates)
    if depth != expected_depth:
        return [
            f"Geometry type '{geom_type}' expects coordinates nested {expected_depth} "
            f"level(s) deep, got {depth if depth >= 0 else 'invalid (non-list)'}"
        ]
    return []


def _coordinate_nesting_depth(value: Any) -> int:
    """Depth of nested lists/tuples down to the innermost numeric pair, or -1 if malformed."""
    if isinstance(value, (list, tuple)):
        if len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
            return 1
        if not value:
            return -1
        inner = _coordinate_nesting_depth(value[0])
        return -1 if inner < 0 else inner + 1
    return -1
