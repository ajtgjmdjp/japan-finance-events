"""Core event models for japan-finance-events."""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Corporate event types."""

    EARNINGS = "earnings"
    FORECAST_REVISION = "forecast_revision"
    DIVIDEND_CHANGE = "dividend_change"
    BUYBACK = "buyback"
    OFFERING = "offering"
    GOVERNANCE = "governance"
    OTHER = "other"


class Direction(str, Enum):
    """Event direction / sentiment."""

    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class SourceType(str, Enum):
    """Data source identifier."""

    TDNET = "tdnet"
    EDINET = "edinet"


class SourceRef(BaseModel):
    """Provenance record linking an event to its original source.

    Attributes:
        source: Data source type (TDNET or EDINET).
        source_id: Original ID from the source system.
        published_at: When this record became publicly available (PIT).
        url: URL to the source document (PDF etc.).
        xbrl_url: URL to XBRL data, if available.
        raw_title: Original title text from the source.
    """

    source: SourceType
    source_id: str
    published_at: datetime
    url: str | None = None
    xbrl_url: str | None = None
    raw_title: str | None = None

    model_config = {"frozen": True}


class Event(BaseModel):
    """A corporate event with Point-in-time timestamp.

    Attributes:
        event_id: Stable canonical ID (auto-generated if not provided).
        event_type: Classification of the event.
        direction: Direction / sentiment (UP, DOWN, NEUTRAL, UNKNOWN).
        company_ticker: 4-digit stock code, if available.
        edinet_code: EDINET code, if available.
        company_name: Company display name.
        pit_published_at: Earliest public timestamp across all sources (PIT).
        fiscal_period_end: End of the fiscal period this event relates to.
        event_date: Date the event occurred (may differ from publish date).
        title: Canonical event title.
        attributes: Extensible key-value store for event-specific data.
        sources: Provenance records from all contributing sources.
    """

    event_id: str = ""
    event_type: EventType
    direction: Direction = Direction.UNKNOWN
    company_ticker: str | None = None
    edinet_code: str | None = None
    company_name: str
    pit_published_at: datetime
    fiscal_period_end: date | None = None
    event_date: date | None = None
    title: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    sources: list[SourceRef] = Field(default_factory=list)

    model_config = {"frozen": True}

    def __init__(self, **data: Any) -> None:
        if not data.get("event_id"):
            data["event_id"] = _generate_event_id(data)
        super().__init__(**data)


def _generate_event_id(data: dict[str, Any]) -> str:
    """Generate a deterministic event ID from key fields.

    Includes title to distinguish multiple events of the same type
    from the same company on the same day (e.g., Q3 earnings + revision).
    """
    parts = [
        data.get("company_ticker") or data.get("edinet_code") or "",
        data.get("event_type", ""),
        str(data.get("pit_published_at", "")),
        data.get("title", ""),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]
