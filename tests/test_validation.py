import pytest

from app.utils.validation import (
    is_within_karachi_bounds,
    validate_confidence,
    validate_data_type,
    validate_geojson_structure,
    validate_market_csv_row,
    validate_property_type,
    validate_transaction_type,
)


def test_is_within_karachi_bounds_true_for_clifton():
    assert is_within_karachi_bounds(24.8138, 67.0300) is True


def test_is_within_karachi_bounds_false_for_far_away_point():
    assert is_within_karachi_bounds(31.5204, 74.3587) is False  # Lahore


@pytest.mark.parametrize(
    "validator,value",
    [
        (validate_property_type, "apartment"),
        (validate_transaction_type, "rent"),
        (validate_confidence, "medium"),
        (validate_data_type, "research_estimate"),
    ],
)
def test_enum_validators_accept_valid_values(validator, value):
    assert validator(value) == value


@pytest.mark.parametrize(
    "validator,value",
    [
        (validate_property_type, "mansion"),
        (validate_transaction_type, "lease"),
        (validate_confidence, "very-high"),
        (validate_data_type, "official"),
    ],
)
def test_enum_validators_reject_invalid_values(validator, value):
    with pytest.raises(ValueError):
        validator(value)


def test_validate_market_csv_row_missing_fields():
    errors = validate_market_csv_row({"location_id": "clifton"})
    assert errors


def test_validate_geojson_structure_rejects_invalid_geometry():
    bad = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": "not-a-list"}, "properties": {}}]}
    errors = validate_geojson_structure(bad)
    assert errors


def test_validate_geojson_structure_accepts_valid_point():
    good = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [67.03, 24.81]},
                "properties": {"location_id": "clifton"},
            }
        ],
    }
    assert validate_geojson_structure(good) == []
