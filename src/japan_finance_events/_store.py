"""In-memory event store with PIT-aware queries."""

from __future__ import annotations

from datetime import datetime
from typing import Iterator

from japan_finance_events._models import Event, EventType


class EventStore:
    """In-memory event store with Point-in-time query support.

    Events are stored in a list sorted by ``pit_published_at``.
    All query methods respect the PIT constraint: only events
    published on or before ``as_of`` are returned.
    """

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._by_id: dict[str, Event] = {}

    def upsert(self, event: Event) -> None:
        """Insert or update an event."""
        existing = self._by_id.get(event.event_id)
        if existing is not None:
            self._events.remove(existing)
        self._by_id[event.event_id] = event
        self._events.append(event)
        self._events.sort(key=lambda e: e.pit_published_at)

    def upsert_many(self, events: list[Event]) -> None:
        """Insert or update multiple events."""
        for event in events:
            existing = self._by_id.get(event.event_id)
            if existing is not None:
                self._events.remove(existing)
            self._by_id[event.event_id] = event
            self._events.append(event)
        self._events.sort(key=lambda e: e.pit_published_at)

    def get(self, event_id: str) -> Event | None:
        """Look up an event by ID."""
        return self._by_id.get(event_id)

    def query(
        self,
        *,
        as_of: datetime | None = None,
        company: str | None = None,
        event_types: set[EventType] | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> list[Event]:
        """Query events with optional PIT constraint.

        Args:
            as_of: Only return events published on or before this time
                (prevents lookahead bias).
            company: Filter by ticker or EDINET code.
            event_types: Filter by event type(s).
            start: Only events published at or after this time.
            end: Only events published at or before this time.
            limit: Maximum number of events to return.

        Returns:
            Events matching filters, sorted by pit_published_at.
        """
        return list(self._iter_filtered(
            as_of=as_of,
            company=company,
            event_types=event_types,
            start=start,
            end=end,
            limit=limit,
        ))

    def iter_pit(
        self,
        *,
        start: datetime,
        end: datetime,
        company: str | None = None,
        event_types: set[EventType] | None = None,
    ) -> Iterator[Event]:
        """Iterate events in PIT order within a time window.

        Yields events with ``start <= pit_published_at <= end``.
        """
        yield from self._iter_filtered(
            as_of=end,
            company=company,
            event_types=event_types,
            start=start,
            end=end,
        )

    def _iter_filtered(
        self,
        *,
        as_of: datetime | None = None,
        company: str | None = None,
        event_types: set[EventType] | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> Iterator[Event]:
        """Internal filtered iterator."""
        count = 0
        for event in self._events:
            if as_of is not None and event.pit_published_at > as_of:
                continue
            if start is not None and event.pit_published_at < start:
                continue
            if end is not None and event.pit_published_at > end:
                continue
            if event_types is not None and event.event_type not in event_types:
                continue
            if company is not None and not _matches_company(event, company):
                continue
            yield event
            count += 1
            if limit is not None and count >= limit:
                return

    def __len__(self) -> int:
        return len(self._events)


def _matches_company(event: Event, company: str) -> bool:
    """Check if event matches a company identifier."""
    return event.company_ticker == company or event.edinet_code == company
