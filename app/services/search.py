"""Fuzzy, case-insensitive search over locations (name/town/slug)."""

from __future__ import annotations

import difflib
from typing import Any

from app.services import data_store


def search_locations(query: str) -> list[dict[str, Any]]:
    """Search locations by substring match first, then fuzzy fallback.

    Returns dicts with id, name, slug, town, score (0-1, higher is better),
    sorted by score descending.
    """
    query_norm = (query or "").strip().lower()
    if not query_norm:
        return []

    locations = data_store.load_locations()
    scored: dict[str, tuple[dict[str, Any], float]] = {}

    for loc in locations:
        fields = [
            str(loc.get("name") or ""),
            str(loc.get("town") or ""),
            str(loc.get("slug") or ""),
        ]
        fields_norm = [f.lower() for f in fields]

        # Substring match: high, exact-ish score.
        if any(query_norm in f for f in fields_norm):
            best_field = min(
                (f for f in fields_norm if query_norm in f),
                key=len,
            )
            score = len(query_norm) / max(len(best_field), 1)
            score = min(1.0, 0.75 + 0.25 * score)  # substring hits rank high
            scored[loc["id"]] = (loc, score)
            continue

        # Fuzzy fallback via difflib.
        best_ratio = 0.0
        for f in fields_norm:
            if not f:
                continue
            ratio = difflib.SequenceMatcher(None, query_norm, f).ratio()
            best_ratio = max(best_ratio, ratio)

        close = difflib.get_close_matches(query_norm, fields_norm, n=1, cutoff=0.5)
        if close or best_ratio >= 0.5:
            scored[loc["id"]] = (loc, best_ratio)

    results = [
        {
            "id": loc.get("id"),
            "name": loc.get("name"),
            "slug": loc.get("slug"),
            "town": loc.get("town"),
            "score": round(score, 4),
        }
        for loc, score in scored.values()
    ]
    results.sort(key=lambda r: r["score"], reverse=True)
    return results
