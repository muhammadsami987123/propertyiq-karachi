"""Raw GeoJSON passthrough endpoints for map rendering."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.services import data_store

router = APIRouter(tags=["geo"])


@router.get("/geo/boundary", response_model=dict[str, Any])
def get_boundary() -> dict[str, Any]:
    return data_store.load_boundary()


@router.get("/geo/localities", response_model=dict[str, Any])
def get_localities() -> dict[str, Any]:
    return data_store.load_localities_geojson()
