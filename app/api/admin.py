"""Admin endpoints: sources listing, location/market upsert, CSV/GeoJSON import.

All endpoints require a valid `X-Admin-Token` header matching
`settings.ADMIN_TOKEN`. Every write persists atomically (temp file +
os.replace) and CSV imports are confined to app/data/market/.
"""

from __future__ import annotations

import csv
import io
import json
import os
import secrets
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File

from app.config import LOCALITIES_FILE, settings
from app.schemas.admin import (
    ImportResult,
    ImportRowError,
    LocationUpsertRequest,
    MarketRecordUpsertRequest,
    SourceOut,
)
from app.services import data_store
from app.services.persistence import (
    atomic_write_json,
    save_locations,
    save_market_records,
    upsert_by_id,
)
from app.utils.validation import validate_geojson_structure, validate_market_csv_row

router = APIRouter(tags=["admin"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    # Use a constant-time comparison so response latency can't leak how many
    # leading characters of a guessed token were correct (timing attack).
    if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid or missing admin token.")


@router.get("/admin/sources", response_model=list[SourceOut], dependencies=[Depends(require_admin_token)])
def list_sources() -> list[dict]:
    return data_store.load_sources()


@router.post("/admin/locations", dependencies=[Depends(require_admin_token)])
def upsert_location(payload: LocationUpsertRequest) -> dict[str, Any]:
    locations = data_store.load_locations()
    updated = upsert_by_id(locations, payload.model_dump())
    save_locations(updated)
    return {"status": "ok", "id": payload.id}


@router.post("/admin/market", dependencies=[Depends(require_admin_token)])
def upsert_market_record(payload: MarketRecordUpsertRequest) -> dict[str, Any]:
    locations = data_store.load_locations()
    if not any(loc.get("id") == payload.location_id for loc in locations):
        raise HTTPException(
            status_code=400,
            detail=f"location_id '{payload.location_id}' does not exist.",
        )

    records = data_store.load_market_records()
    updated = upsert_by_id(records, payload.model_dump())
    save_market_records(updated)
    return {"status": "ok", "id": payload.id}


def _sanitize_filename(filename: str | None) -> str:
    """Reduce a client-provided filename to a safe basename only."""
    if not filename:
        return "upload"
    return os.path.basename(filename)


@router.post(
    "/admin/import/csv",
    response_model=ImportResult,
    dependencies=[Depends(require_admin_token)],
)
async def import_csv(file: UploadFile = File(...)) -> dict[str, Any]:
    safe_name = _sanitize_filename(file.filename)
    if not safe_name.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds the 5MB size limit.")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not valid UTF-8 text.")

    reader = csv.DictReader(io.StringIO(text))
    existing = data_store.load_locations()
    valid_location_ids = {loc.get("id") for loc in existing}

    records = data_store.load_market_records()
    errors: list[dict[str, Any]] = []
    imported = 0

    for row_number, row in enumerate(reader, start=2):  # header is row 1
        row_errors = validate_market_csv_row(row)
        if row.get("location_id") and row["location_id"] not in valid_location_ids:
            row_errors.append(f"Unknown location_id '{row['location_id']}'")

        if row_errors:
            errors.append({"row": row_number, "message": "; ".join(row_errors)})
            continue

        record = dict(row)
        for numeric_field in (
            "price_min",
            "price_max",
            "price_avg",
            "price_per_sqft_min",
            "price_per_sqft_max",
            "observations",
        ):
            if record.get(numeric_field) not in (None, ""):
                try:
                    record[numeric_field] = float(record[numeric_field])
                except ValueError:
                    pass
        record.setdefault("currency", "PKR")

        records = upsert_by_id(records, record)
        imported += 1

    save_market_records(records)

    return {
        "imported": imported,
        "errors": [ImportRowError(**e) for e in errors],
    }


@router.post(
    "/admin/import/geojson",
    dependencies=[Depends(require_admin_token)],
)
async def import_geojson(file: UploadFile = File(...)) -> dict[str, Any]:
    safe_name = _sanitize_filename(file.filename)
    if not (safe_name.lower().endswith(".geojson") or safe_name.lower().endswith(".json")):
        raise HTTPException(status_code=400, detail="Only .geojson or .json files are accepted.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds the 5MB size limit.")

    try:
        payload = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail=f"File is not valid JSON: {exc}")

    errors = validate_geojson_structure(payload)
    if errors:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid GeoJSON structure.", "errors": errors},
        )

    # Merge into localities.geojson: upsert features by properties.location_id.
    current = data_store.load_localities_geojson()
    current_features = current.get("features", []) if isinstance(current, dict) else []

    incoming_features = (
        payload.get("features", []) if payload.get("type") == "FeatureCollection" else [payload]
    )

    by_location_id = {
        f.get("properties", {}).get("location_id"): f
        for f in current_features
        if isinstance(f, dict)
    }
    for feature in incoming_features:
        location_id = feature.get("properties", {}).get("location_id")
        if location_id:
            by_location_id[location_id] = feature
        else:
            by_location_id[id(feature)] = feature

    merged = {"type": "FeatureCollection", "features": list(by_location_id.values())}
    atomic_write_json(LOCALITIES_FILE, merged)

    return {"status": "ok", "features_imported": len(incoming_features)}
