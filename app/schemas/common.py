"""Shared API response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard JSON error envelope (never a raw stack trace)."""

    detail: str
