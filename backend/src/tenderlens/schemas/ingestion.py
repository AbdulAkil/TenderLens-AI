from typing import Literal

from pydantic import BaseModel, Field


class TedIngestionRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2_000)
    scope: Literal["ACTIVE", "ALL"] = "ACTIVE"
    max_notices: int = Field(default=250, ge=1, le=5_000)
    page_size: int = Field(default=100, ge=1, le=250)
    only_latest_versions: bool = True


class TedIngestionResponse(BaseModel):
    fetched: int
    inserted: int
    updated: int
    unchanged: int = 0
    total_matches: int | None
    complete: bool
