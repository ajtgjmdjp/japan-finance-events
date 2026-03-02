"""Tests for event deduplication."""

from __future__ import annotations

from datetime import date, datetime

from japan_finance_events import Direction, Event, EventType, SourceRef, SourceType
from japan_finance_events._dedupe import dedupe_score, deduplicate, merge_events


class TestDedupeScore:
    def test_same_company_same_type_same_day(self) -> None:
        """Identical events should score >= threshold."""
        a = Event(
            event_type=EventType.EARNINGS,
            company_ticker="7203",
            company_name="トヨタ",
            pit_published_at=datetime(2026, 2, 10),
            title="決算短信 (TDNET)",
        )
        b = Event(
            event_type=EventType.EARNINGS,
            company_ticker="7203",
            company_name="トヨタ",
            pit_published_at=datetime(2026, 2, 10),
            title="有価証券報告書 (EDINET)",
        )
        assert dedupe_score(a, b) >= 0.75

    def test_different_company(self) -> None:
        a = Event(
            event_type=EventType.EARNINGS,
            company_ticker="7203",
            company_name="トヨタ",
            pit_published_at=datetime(2026, 2, 10),
            title="決算",
        )
        b = Event(
            event_type=EventType.EARNINGS,
            company_ticker="6758",
            company_name="ソニー",
            pit_published_at=datetime(2026, 2, 10),
            title="決算",
        )
        assert dedupe_score(a, b) < 0.75

    def test_different_type(self) -> None:
        a = Event(
            event_type=EventType.EARNINGS,
            company_ticker="7203",
            company_name="トヨタ",
            pit_published_at=datetime(2026, 2, 10),
            title="決算",
        )
        b = Event(
            event_type=EventType.BUYBACK,
            company_ticker="7203",
            company_name="トヨタ",
            pit_published_at=datetime(2026, 2, 10),
            title="自己株式取得",
        )
        assert dedupe_score(a, b) < 0.75

    def test_edinet_code_match(self) -> None:
        """Match by EDINET code when ticker is absent."""
        a = Event(
            event_type=EventType.EARNINGS,
            edinet_code="E02144",
            company_name="トヨタ",
            pit_published_at=datetime(2026, 2, 10),
            title="決算",
        )
        b = Event(
            event_type=EventType.EARNINGS,
            edinet_code="E02144",
            company_name="トヨタ",
            pit_published_at=datetime(2026, 2, 11),
            title="有報",
        )
        assert dedupe_score(a, b) >= 0.75

    def test_fiscal_period_bonus(self) -> None:
        a = Event(
            event_type=EventType.EARNINGS,
            company_ticker="7203",
            company_name="トヨタ",
            pit_published_at=datetime(2026, 2, 10),
            fiscal_period_end=date(2026, 3, 31),
            title="決算",
        )
        b = Event(
            event_type=EventType.EARNINGS,
            company_ticker="7203",
            company_name="トヨタ",
            pit_published_at=datetime(2026, 2, 10),
            fiscal_period_end=date(2026, 3, 31),
            title="有報",
        )
        score = dedupe_score(a, b)
        assert score == 1.0


class TestMergeEvents:
    def test_merge_keeps_earliest_pit(self) -> None:
        a = Event(
            event_id="e1",
            event_type=EventType.EARNINGS,
            company_ticker="7203",
            company_name="トヨタ",
            pit_published_at=datetime(2026, 2, 10),
            title="決算短信",
            sources=[
                SourceRef(
                    source=SourceType.TDNET,
                    source_id="TD1",
                    published_at=datetime(2026, 2, 10),
                ),
            ],
        )
        b = Event(
            event_id="e2",
            event_type=EventType.EARNINGS,
            edinet_code="E02144",
            company_name="トヨタ自動車株式会社",
            pit_published_at=datetime(2026, 2, 12),
            title="有価証券報告書",
            sources=[
                SourceRef(
                    source=SourceType.EDINET,
                    source_id="S100ABC",
                    published_at=datetime(2026, 2, 12),
                ),
            ],
        )
        merged = merge_events(a, b)
        assert merged.pit_published_at == datetime(2026, 2, 10)
        assert merged.company_ticker == "7203"
        assert merged.edinet_code == "E02144"
        assert len(merged.sources) == 2

    def test_merge_prefers_primary_direction(self) -> None:
        a = Event(
            event_type=EventType.FORECAST_REVISION,
            direction=Direction.UP,
            company_name="テスト",
            pit_published_at=datetime(2026, 1, 1),
            title="上方修正",
        )
        b = Event(
            event_type=EventType.FORECAST_REVISION,
            direction=Direction.UNKNOWN,
            company_name="テスト",
            pit_published_at=datetime(2026, 1, 1),
            title="修正",
        )
        merged = merge_events(a, b)
        assert merged.direction == Direction.UP

    def test_merge_fills_direction_from_secondary(self) -> None:
        a = Event(
            event_type=EventType.FORECAST_REVISION,
            direction=Direction.UNKNOWN,
            company_name="テスト",
            pit_published_at=datetime(2026, 1, 1),
            title="修正",
        )
        b = Event(
            event_type=EventType.FORECAST_REVISION,
            direction=Direction.DOWN,
            company_name="テスト",
            pit_published_at=datetime(2026, 1, 1),
            title="下方修正",
        )
        merged = merge_events(a, b)
        assert merged.direction == Direction.DOWN


class TestDeduplicate:
    def test_no_duplicates(self) -> None:
        events = [
            Event(
                event_type=EventType.EARNINGS,
                company_ticker="7203",
                company_name="トヨタ",
                pit_published_at=datetime(2026, 2, 10),
                title="決算",
            ),
            Event(
                event_type=EventType.BUYBACK,
                company_ticker="6758",
                company_name="ソニー",
                pit_published_at=datetime(2026, 2, 15),
                title="自社株買い",
            ),
        ]
        result = deduplicate(events)
        assert len(result) == 2

    def test_merges_duplicates(self) -> None:
        events = [
            Event(
                event_type=EventType.EARNINGS,
                company_ticker="7203",
                company_name="トヨタ",
                pit_published_at=datetime(2026, 2, 10),
                title="決算短信",
                sources=[
                    SourceRef(
                        source=SourceType.TDNET,
                        source_id="TD1",
                        published_at=datetime(2026, 2, 10),
                    ),
                ],
            ),
            Event(
                event_type=EventType.EARNINGS,
                company_ticker="7203",
                company_name="トヨタ自動車",
                pit_published_at=datetime(2026, 2, 11),
                title="有価証券報告書",
                sources=[
                    SourceRef(
                        source=SourceType.EDINET,
                        source_id="S100",
                        published_at=datetime(2026, 2, 11),
                    ),
                ],
            ),
        ]
        result = deduplicate(events)
        assert len(result) == 1
        assert len(result[0].sources) == 2

    def test_empty_list(self) -> None:
        assert deduplicate([]) == []

    def test_sorted_output(self) -> None:
        events = [
            Event(
                event_type=EventType.EARNINGS,
                company_ticker="6758",
                company_name="ソニー",
                pit_published_at=datetime(2026, 3, 1),
                title="決算",
            ),
            Event(
                event_type=EventType.BUYBACK,
                company_ticker="7203",
                company_name="トヨタ",
                pit_published_at=datetime(2026, 1, 1),
                title="自社株買い",
            ),
        ]
        result = deduplicate(events)
        assert result[0].pit_published_at < result[1].pit_published_at
