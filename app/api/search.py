"""Fuzzy locality search endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.search import SearchResult
from app.services.search import search_locations

router = APIRouter(tags=["search"])


@router.get("/search", response_model=list[SearchResult])
def search(q: str = Query(default="", description="Search query")) -> list[dict]:
    return search_locations(q)
