from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import DISCLAIMER


class BriefSource(BaseModel):
    index: int = Field(description="Reference number used in the brief text, e.g. [1]")
    headline: str
    publisher: str | None = None
    published_at: datetime | None = None
    source_url: str | None = None


class AiBriefResponse(BaseModel):
    ticker: str
    company_name: str
    brief_text: str = Field(description="Markdown narrative. Figures cite sources as [n].")
    sources: list[BriefSource] = Field(default_factory=list)
    as_of: datetime = Field(description="UTC timestamp of the underlying market data.")
    generated_at: datetime
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    disclaimer: str = Field(default=DISCLAIMER)
