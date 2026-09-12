"""Atomic writes and upsert helpers for the JSON data files.

All admin write endpoints funnel through here so that persistence is always
atomic (write to a temp file in the same directory, then os.replace) and
imports are always confined to app/data/market/.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from app.config import LOCATIONS_FILE, MARKET_FILE


def atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON to `path` atomically (temp file + os.replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


def upsert_by_id(records: list[dict[str, Any]], new_record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a new list with new_record inserted or replacing an existing id."""
    result = [r for r in records if r.get("id") != new_record.get("id")]
    result.append(new_record)
    return result


def save_locations(locations: list[dict[str, Any]]) -> None:
    atomic_write_json(LOCATIONS_FILE, locations)


def save_market_records(records: list[dict[str, Any]]) -> None:
    atomic_write_json(MARKET_FILE, records)
