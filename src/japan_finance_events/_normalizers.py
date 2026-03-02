"""Normalizers that convert raw TDNET/EDINET data into canonical Events."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from japan_finance_events._models import (
    Direction,
    Event,
    EventType,
    SourceRef,
    SourceType,
)

# ---------------------------------------------------------------------------
# Direction classification (rule-based)
# ---------------------------------------------------------------------------

_UPWARD_PATTERNS = re.compile(r"上方修正|増配|増額|上振れ")
_DOWNWARD_PATTERNS = re.compile(r"下方修正|減配|減額|下振れ|無配")


def classify_direction(title: str, event_type: EventType) -> Direction:
    """Classify event direction from title text (rule-based).

    Only classifies FORECAST_REVISION and DIVIDEND_CHANGE events.
    All others default to UNKNOWN.
    """
    if event_type not in (EventType.FORECAST_REVISION, EventType.DIVIDEND_CHANGE):
        return Direction.UNKNOWN
    if _UPWARD_PATTERNS.search(title):
        return Direction.UP
    if _DOWNWARD_PATTERNS.search(title):
        return Direction.DOWN
    return Direction.UNKNOWN


# ---------------------------------------------------------------------------
# TDNET category → EventType mapping
# ---------------------------------------------------------------------------

_TDNET_CATEGORY_MAP: dict[str, EventType] = {
    "earnings": EventType.EARNINGS,
    "dividend": EventType.DIVIDEND_CHANGE,
    "forecast_revision": EventType.FORECAST_REVISION,
    "buyback": EventType.BUYBACK,
    "offering": EventType.OFFERING,
    "governance": EventType.GOVERNANCE,
    "other": EventType.OTHER,
}

# ---------------------------------------------------------------------------
# EDINET DocType → EventType mapping
# ---------------------------------------------------------------------------

_EDINET_DOCTYPE_MAP: dict[str, EventType] = {
    "120": EventType.EARNINGS,  # 有価証券報告書 (annual)
    "140": EventType.EARNINGS,  # 四半期報告書
    "160": EventType.EARNINGS,  # 半期報告書
    "180": EventType.OTHER,  # 臨時報告書
}


def from_tdnet_disclosure(disclosure: dict[str, Any]) -> Event:
    """Convert a TDNET disclosure dict to a canonical Event.

    Expected keys: id, pubdate, company_code, company_name,
    title, category, document_url.
    """
    category = disclosure.get("category", "other")
    event_type = _TDNET_CATEGORY_MAP.get(category, EventType.OTHER)
    title = disclosure.get("title", "")
    direction = classify_direction(title, event_type)

    pubdate_raw = disclosure.get("pubdate", "")
    if isinstance(pubdate_raw, datetime):
        pit = pubdate_raw
    else:
        pit = datetime.fromisoformat(str(pubdate_raw))

    source_ref = SourceRef(
        source=SourceType.TDNET,
        source_id=disclosure.get("id", ""),
        published_at=pit,
        url=disclosure.get("document_url"),
        xbrl_url=disclosure.get("xbrl_url"),
        raw_title=title,
    )

    return Event(
        event_type=event_type,
        direction=direction,
        company_ticker=disclosure.get("company_code"),
        company_name=disclosure.get("company_name", ""),
        pit_published_at=pit,
        title=title,
        sources=[source_ref],
    )


def from_edinet_filing(filing: dict[str, Any]) -> Event:
    """Convert an EDINET filing dict to a canonical Event.

    Expected keys: doc_id, edinet_code, company_name,
    doc_type (code string), filing_date, period_end.
    """
    doc_type_code = filing.get("doc_type", "000")
    event_type = _EDINET_DOCTYPE_MAP.get(doc_type_code, EventType.OTHER)
    title = filing.get("description", "") or f"EDINET Filing {doc_type_code}"
    direction = classify_direction(title, event_type)

    filing_date = filing.get("filing_date", "")
    if isinstance(filing_date, datetime):
        pit = filing_date
    else:
        pit = datetime.fromisoformat(str(filing_date))

    period_end = filing.get("period_end")

    source_ref = SourceRef(
        source=SourceType.EDINET,
        source_id=filing.get("doc_id", ""),
        published_at=pit,
        raw_title=title,
    )

    return Event(
        event_type=event_type,
        direction=direction,
        edinet_code=filing.get("edinet_code"),
        company_name=filing.get("company_name", ""),
        pit_published_at=pit,
        fiscal_period_end=period_end,
        title=title,
        sources=[source_ref],
    )
