"""Shared test fixtures for japan-finance-events."""

from __future__ import annotations

from datetime import datetime

import pytest

from japan_finance_events import Event, EventStore, EventType, SourceRef, SourceType


@pytest.fixture()
def sample_events() -> list[Event]:
    return [
        Event(
            event_type=EventType.EARNINGS,
            company_ticker="7203",
            company_name="トヨタ自動車株式会社",
            pit_published_at=datetime(2026, 2, 10, 15, 0),
            title="2026年3月期 第3四半期決算短信",
            sources=[
                SourceRef(
                    source=SourceType.TDNET,
                    source_id="TD001",
                    published_at=datetime(2026, 2, 10, 15, 0),
                    raw_title="2026年3月期 第3四半期決算短信",
                ),
            ],
        ),
        Event(
            event_type=EventType.FORECAST_REVISION,
            direction="up",
            company_ticker="6758",
            company_name="ソニーグループ株式会社",
            pit_published_at=datetime(2026, 2, 15, 16, 0),
            title="業績予想の上方修正に関するお知らせ",
            sources=[
                SourceRef(
                    source=SourceType.TDNET,
                    source_id="TD002",
                    published_at=datetime(2026, 2, 15, 16, 0),
                    raw_title="業績予想の上方修正に関するお知らせ",
                ),
            ],
        ),
        Event(
            event_type=EventType.DIVIDEND_CHANGE,
            direction="down",
            company_ticker="7203",
            company_name="トヨタ自動車株式会社",
            pit_published_at=datetime(2026, 3, 1, 10, 0),
            title="配当予想の修正（減配）に関するお知らせ",
            sources=[
                SourceRef(
                    source=SourceType.TDNET,
                    source_id="TD003",
                    published_at=datetime(2026, 3, 1, 10, 0),
                    raw_title="配当予想の修正（減配）に関するお知らせ",
                ),
            ],
        ),
    ]


@pytest.fixture()
def store(sample_events: list[Event]) -> EventStore:
    s = EventStore()
    s.upsert_many(sample_events)
    return s
