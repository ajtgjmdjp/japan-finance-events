"""Tests for EventStore."""

from __future__ import annotations

from datetime import datetime

from japan_finance_events import Event, EventStore, EventType


class TestStore:
    def test_upsert_and_get(self) -> None:
        store = EventStore()
        event = Event(
            event_id="e1",
            event_type=EventType.EARNINGS,
            company_name="テスト",
            pit_published_at=datetime(2026, 1, 1),
            title="決算",
        )
        store.upsert(event)
        assert store.get("e1") is not None
        assert len(store) == 1

    def test_upsert_replaces(self) -> None:
        store = EventStore()
        e1 = Event(
            event_id="e1",
            event_type=EventType.EARNINGS,
            company_name="テスト",
            pit_published_at=datetime(2026, 1, 1),
            title="決算v1",
        )
        e2 = Event(
            event_id="e1",
            event_type=EventType.EARNINGS,
            company_name="テスト更新",
            pit_published_at=datetime(2026, 1, 1),
            title="決算v2",
        )
        store.upsert(e1)
        store.upsert(e2)
        assert len(store) == 1
        assert store.get("e1") is not None
        assert store.get("e1").company_name == "テスト更新"  # type: ignore[union-attr]

    def test_query_all(self, store: EventStore) -> None:
        assert len(store.query()) == 3

    def test_query_by_company(self, store: EventStore) -> None:
        results = store.query(company="7203")
        assert len(results) == 2
        assert all(e.company_ticker == "7203" for e in results)

    def test_query_by_event_type(self, store: EventStore) -> None:
        results = store.query(event_types={EventType.EARNINGS})
        assert len(results) == 1
        assert results[0].event_type == EventType.EARNINGS

    def test_query_as_of_pit(self, store: EventStore) -> None:
        """as_of prevents lookahead."""
        results = store.query(as_of=datetime(2026, 2, 12))
        assert len(results) == 1  # Only the Feb 10 event

    def test_query_time_range(self, store: EventStore) -> None:
        results = store.query(
            start=datetime(2026, 2, 1),
            end=datetime(2026, 2, 28),
        )
        assert len(results) == 2

    def test_query_limit(self, store: EventStore) -> None:
        results = store.query(limit=1)
        assert len(results) == 1

    def test_query_combined_filters(self, store: EventStore) -> None:
        results = store.query(
            company="7203",
            event_types={EventType.DIVIDEND_CHANGE},
        )
        assert len(results) == 1
        assert results[0].event_type == EventType.DIVIDEND_CHANGE

    def test_iter_pit(self, store: EventStore) -> None:
        events = list(store.iter_pit(
            start=datetime(2026, 2, 1),
            end=datetime(2026, 2, 28),
        ))
        assert len(events) == 2

    def test_sorted_by_pit(self, store: EventStore) -> None:
        results = store.query()
        timestamps = [e.pit_published_at for e in results]
        assert timestamps == sorted(timestamps)

    def test_get_not_found(self, store: EventStore) -> None:
        assert store.get("nonexistent") is None
