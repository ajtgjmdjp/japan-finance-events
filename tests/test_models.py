"""Tests for event models."""

from __future__ import annotations

from datetime import datetime

from japan_finance_events import (
    Direction,
    Event,
    EventType,
    SourceRef,
    SourceType,
)


class TestEvent:
    def test_auto_event_id(self) -> None:
        """Event ID is auto-generated when not provided."""
        event = Event(
            event_type=EventType.EARNINGS,
            company_ticker="7203",
            company_name="トヨタ",
            pit_published_at=datetime(2026, 2, 10),
            title="決算短信",
        )
        assert event.event_id
        assert len(event.event_id) == 12

    def test_deterministic_event_id(self) -> None:
        """Same inputs produce the same event ID."""
        kwargs = {
            "event_type": EventType.EARNINGS,
            "company_ticker": "7203",
            "company_name": "トヨタ",
            "pit_published_at": datetime(2026, 2, 10),
            "title": "決算短信",
        }
        e1 = Event(**kwargs)
        e2 = Event(**kwargs)
        assert e1.event_id == e2.event_id

    def test_explicit_event_id(self) -> None:
        """Explicit event ID is preserved."""
        event = Event(
            event_id="custom-id",
            event_type=EventType.BUYBACK,
            company_name="テスト",
            pit_published_at=datetime(2026, 1, 1),
            title="自己株式取得",
        )
        assert event.event_id == "custom-id"

    def test_default_direction(self) -> None:
        """Direction defaults to UNKNOWN."""
        event = Event(
            event_type=EventType.EARNINGS,
            company_name="テスト",
            pit_published_at=datetime(2026, 1, 1),
            title="決算短信",
        )
        assert event.direction == Direction.UNKNOWN

    def test_frozen_model(self) -> None:
        """Event is immutable."""
        event = Event(
            event_type=EventType.EARNINGS,
            company_name="テスト",
            pit_published_at=datetime(2026, 1, 1),
            title="決算短信",
        )
        try:
            event.title = "changed"  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except Exception:
            pass


class TestSourceRef:
    def test_creation(self) -> None:
        ref = SourceRef(
            source=SourceType.TDNET,
            source_id="TD001",
            published_at=datetime(2026, 2, 10),
        )
        assert ref.source == SourceType.TDNET
        assert ref.url is None

    def test_frozen(self) -> None:
        ref = SourceRef(
            source=SourceType.EDINET,
            source_id="S100ABC",
            published_at=datetime(2026, 2, 10),
        )
        try:
            ref.source_id = "changed"  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except Exception:
            pass
