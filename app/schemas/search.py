"""API schemas for search endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class SearchResult(BaseModel):
    id: str
    name: str
    slug: str
    town: str | None = None
    score: float
