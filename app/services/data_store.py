"""Defensive JSON/GeoJSON loading for the shared data contract.

Data files are produced by a parallel data-authoring process and may not
exist yet (or may be temporarily mid-write). Every loader here degrades
gracefully: a missing or malformed file logs a warning and yields an empty
result instead of crashing the app.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.config import (
    BOUNDARY_FILE,
    LOCALITIES_FILE,
    LOCATIONS_FILE,
    MARKET_FILE,
    SOURCES_FILE,
    TRENDS_FILE,
)

logger = logging.getLogger("propertyiq.data_store")


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        logger.warning("Data file not found, serving empty result: %s", path)
        return default
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load data file %s: %s", path, exc)
        return default


def load_locations() -> list[dict[str, Any]]:
    data = _load_json(LOCATIONS_FILE, [])
    return data if isinstance(data, list) else []


def load_market_records() -> list[dict[str, Any]]:
    data = _load_json(MARKET_FILE, [])
    return data if isinstance(data, list) else []


def load_trends() -> list[dict[str, Any]]:
    data = _load_json(TRENDS_FILE, [])
    return data if isinstance(data, list) else []


def load_sources() -> list[dict[str, Any]]:
    data = _load_json(SOURCES_FILE, [])
    return data if isinstance(data, list) else []


def load_boundary() -> dict[str, Any]:
    data = _load_json(BOUNDARY_FILE, {})
    return data if isinstance(data, dict) else {}


def load_localities_geojson() -> dict[str, Any]:
    data = _load_json(
        LOCALITIES_FILE, {"type": "FeatureCollection", "features": []}
    )
    return data if isinstance(data, dict) else {"type": "FeatureCollection", "features": []}
