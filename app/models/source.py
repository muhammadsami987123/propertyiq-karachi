"""Internal domain model for a data source citation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Source(BaseModel):
    """A source record as stored in sources.json."""

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    url: str | None = None
    type: str
    description: str | None = None
    terms_note: str | None = None
