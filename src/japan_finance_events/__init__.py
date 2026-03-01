"""japan-finance-events: Event-driven corporate event dataset for Japanese financial data.

Extract and structure corporate events (earnings, forecast revisions,
buybacks, dividend changes) from TDNET and EDINET with Point-in-time
timestamps to prevent lookahead bias in backtesting.

Quick start::

    from japan_finance_events import Event, EventStore, EventType

    store = EventStore()
    events = store.query(company="7203", event_types={EventType.EARNINGS})
"""

from japan_finance_events._dedupe import deduplicate
from japan_finance_events._models import (
    Direction,
    Event,
    EventType,
    SourceRef,
    SourceType,
)
from japan_finance_events._normalizers import (
    classify_direction,
    from_edinet_filing,
    from_tdnet_disclosure,
)
from japan_finance_events._store import EventStore

__all__ = [
    "Direction",
    "Event",
    "EventStore",
    "EventType",
    "SourceRef",
    "SourceType",
    "classify_direction",
    "deduplicate",
    "from_edinet_filing",
    "from_tdnet_disclosure",
]
__version__ = "0.1.0"
