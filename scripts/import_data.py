#!/usr/bin/env python3
"""
import_data.py — Import new market-data or location rows into PropertyIQ's
flat-file Karachi dataset.

Examples:
    python scripts/import_data.py --file new_data.csv --type market
    python scripts/import_data.py --file new_locations.json --type locations

Rows are validated against the same schema rules used by
scripts/validate_data.py, upserted into the target JSON file, and written
atomically (temp file + os.replace) so a crash mid-write never corrupts the
existing dataset. Rows referencing unknown location_ids are skipped with a
warning rather than failing the whole import.

Stdlib only — no pandas, no third-party dependency.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

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

LAT_MIN, LAT_MAX = 24.7, 25.2
LON_MIN, LON_MAX = 66.6, 67.5

NUMERIC_MARKET_FIELDS = (
    "price_min",
    "price_max",
    "price_avg",
    "price_per_sqft_min",
    "price_per_sqft_max",
    "observations",
)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def coerce_numeric_fields(row: dict, fields: tuple[str, ...]) -> None:
    """CSV rows arrive as strings; coerce known-numeric fields in place."""
    for field in fields:
        if field in row and row[field] not in (None, ""):
            try:
                row[field] = float(row[field])
                if row[field] == int(row[field]):
                    row[field] = int(row[field])
            except (TypeError, ValueError):
                pass  # leave as-is; validation will flag it
        elif field in row and row[field] == "":
            row[field] = None


def load_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            rows = [dict(r) for r in reader]
        for row in rows:
            coerce_numeric_fields(row, NUMERIC_MARKET_FIELDS)
            coerce_numeric_fields(row, ("latitude", "longitude"))
            if "nearby_ids" in row and isinstance(row["nearby_ids"], str):
                row["nearby_ids"] = [x.strip() for x in row["nearby_ids"].split("|") if x.strip()]
        return rows
    elif path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise ValueError("JSON input must be an array of objects or a single object")
        return data
    else:
        raise ValueError(f"Unsupported file extension: {path.suffix} (use .csv or .json)")


def validate_market_row(row: dict, location_ids: set[str], errors: list[str], idx: int) -> bool:
    required = [
        "location_id",
        "property_type",
        "transaction_type",
        "price_min",
        "price_max",
        "price_avg",
        "data_type",
        "confidence",
    ]
    ok = True
    for field in required:
        if row.get(field) in (None, ""):
            errors.append(f"row {idx}: missing required field '{field}'")
            ok = False
    if not ok:
        return False

    if location_ids and row["location_id"] not in location_ids:
        errors.append(f"row {idx}: unknown location_id '{row['location_id']}' (skipped)")
        return False
    if row["property_type"] not in PROPERTY_TYPES:
        errors.append(f"row {idx}: invalid property_type '{row['property_type']}'")
        ok = False
    if row["transaction_type"] not in TRANSACTION_TYPES:
        errors.append(f"row {idx}: invalid transaction_type '{row['transaction_type']}'")
        ok = False
    if row["data_type"] not in DATA_TYPES:
        errors.append(f"row {idx}: invalid data_type '{row['data_type']}'")
        ok = False
    if row["confidence"] not in CONFIDENCE_LEVELS:
        errors.append(f"row {idx}: invalid confidence '{row['confidence']}'")
        ok = False

    price_min, price_max, price_avg = row.get("price_min"), row.get("price_max"), row.get("price_avg")
    if not all(is_number(v) for v in (price_min, price_max, price_avg)):
        errors.append(f"row {idx}: price_min/price_max/price_avg must be numeric")
        ok = False
    else:
        if price_min < 0 or price_max < 0 or price_avg < 0:
            errors.append(f"row {idx}: prices must be non-negative")
            ok = False
        if not (price_min <= price_avg <= price_max):
            errors.append(f"row {idx}: expected price_min <= price_avg <= price_max")
            ok = False

    sqft_min, sqft_max = row.get("price_per_sqft_min"), row.get("price_per_sqft_max")
    if is_number(sqft_min) and is_number(sqft_max) and sqft_min > sqft_max:
        errors.append(f"row {idx}: price_per_sqft_min must be <= price_per_sqft_max")
        ok = False

    row.setdefault("currency", "PKR")
    if row["currency"] != "PKR":
        errors.append(f"row {idx}: currency must be 'PKR'")
        ok = False

    return ok


def validate_location_row(row: dict, errors: list[str], idx: int) -> bool:
    required = ["id", "slug", "name", "city", "latitude", "longitude", "market_category"]
    ok = True
    for field in required:
        if row.get(field) in (None, ""):
            errors.append(f"row {idx}: missing required field '{field}'")
            ok = False
    if not ok:
        return False

    if row["market_category"] not in MARKET_CATEGORIES:
        errors.append(f"row {idx}: invalid market_category '{row['market_category']}'")
        ok = False

    lat, lon = row.get("latitude"), row.get("longitude")
    if not is_number(lat) or not is_number(lon):
        errors.append(f"row {idx}: latitude/longitude must be numeric")
        ok = False
    else:
        if not (LAT_MIN <= lat <= LAT_MAX):
            errors.append(f"row {idx}: latitude {lat} outside Karachi bounds")
            ok = False
        if not (LON_MIN <= lon <= LON_MAX):
            errors.append(f"row {idx}: longitude {lon} outside Karachi bounds")
            ok = False

    row.setdefault("nearby_ids", [])
    return ok


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp_path, path)


def import_market(
    input_rows: list[dict], data_dir: Path
) -> tuple[int, int, int, list[str]]:
    locations_path = data_dir / "locations" / "karachi_locations.json"
    market_path = data_dir / "market" / "karachi_market_data.json"

    existing_locations: list[dict] = []
    if locations_path.exists():
        try:
            existing_locations = json.loads(locations_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing_locations = []
    location_ids = {loc["id"] for loc in existing_locations if isinstance(loc, dict) and "id" in loc}

    existing_market: list[dict] = []
    if market_path.exists():
        try:
            existing_market = json.loads(market_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing_market = []
    by_id = {rec["id"]: rec for rec in existing_market if isinstance(rec, dict) and "id" in rec}

    errors: list[str] = []
    imported = 0
    skipped = 0

    for idx, row in enumerate(input_rows, start=1):
        row = dict(row)
        if not row.get("id"):
            row["id"] = f"{row.get('location_id')}-{row.get('property_type')}-{row.get('transaction_type')}"

        if not validate_market_row(row, location_ids, errors, idx):
            skipped += 1
            continue

        by_id[row["id"]] = row
        imported += 1

    merged = list(by_id.values())
    atomic_write_json(market_path, merged)
    return len(input_rows), imported, skipped, errors


def import_locations(input_rows: list[dict], data_dir: Path) -> tuple[int, int, int, list[str]]:
    locations_path = data_dir / "locations" / "karachi_locations.json"

    existing_locations: list[dict] = []
    if locations_path.exists():
        try:
            existing_locations = json.loads(locations_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing_locations = []
    by_id = {loc["id"]: loc for loc in existing_locations if isinstance(loc, dict) and "id" in loc}

    errors: list[str] = []
    imported = 0
    skipped = 0

    for idx, row in enumerate(input_rows, start=1):
        row = dict(row)
        if not validate_location_row(row, errors, idx):
            skipped += 1
            continue
        by_id[row["id"]] = row
        imported += 1

    merged = list(by_id.values())
    atomic_write_json(locations_path, merged)
    return len(input_rows), imported, skipped, errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import market-data or location rows into PropertyIQ's Karachi dataset."
    )
    parser.add_argument("--file", required=True, help="Path to a CSV or JSON file to import")
    parser.add_argument(
        "--type",
        required=True,
        choices=["market", "locations"],
        help="What kind of records the file contains",
    )
    parser.add_argument(
        "--data-dir",
        default="app/data",
        help="Path to the app/data directory (default: app/data)",
    )
    args = parser.parse_args()

    input_path = Path(args.file)
    data_dir = Path(args.data_dir)

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        rows = load_rows(input_path)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Error: could not read input file: {exc}", file=sys.stderr)
        return 1

    if args.type == "market":
        total, imported, skipped, errors = import_market(rows, data_dir)
        target = data_dir / "market" / "karachi_market_data.json"
    else:
        total, imported, skipped, errors = import_locations(rows, data_dir)
        target = data_dir / "locations" / "karachi_locations.json"

    print(f"Import summary ({args.type}):")
    print(f"  Rows read:     {total}")
    print(f"  Imported:      {imported}")
    print(f"  Skipped:       {skipped}")
    print(f"  Written to:    {target}")

    if errors:
        print(f"\nWarnings/errors ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
