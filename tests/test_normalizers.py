"""Tests for normalizers and direction classification."""

from __future__ import annotations

from japan_finance_events import (
    Direction,
    EventType,
    classify_direction,
    from_edinet_filing,
    from_tdnet_disclosure,
)


class TestClassifyDirection:
    def test_upward_revision(self) -> None:
        assert (
            classify_direction("業績予想の上方修正に関するお知らせ", EventType.FORECAST_REVISION)
            == Direction.UP
        )

    def test_downward_revision(self) -> None:
        assert (
            classify_direction(
                "通期業績予想の下方修正に関するお知らせ", EventType.FORECAST_REVISION
            )
            == Direction.DOWN
        )

    def test_dividend_increase(self) -> None:
        assert (
            classify_direction("増配に関するお知らせ", EventType.DIVIDEND_CHANGE) == Direction.UP
        )

    def test_dividend_decrease(self) -> None:
        assert (
            classify_direction("減配に関するお知らせ", EventType.DIVIDEND_CHANGE) == Direction.DOWN
        )

    def test_no_dividend(self) -> None:
        assert (
            classify_direction("無配に関するお知らせ", EventType.DIVIDEND_CHANGE) == Direction.DOWN
        )

    def test_earnings_always_unknown(self) -> None:
        """Direction is only classified for revisions and dividends."""
        assert classify_direction("上方修正", EventType.EARNINGS) == Direction.UNKNOWN

    def test_neutral_revision(self) -> None:
        """No keyword match → UNKNOWN."""
        assert (
            classify_direction("業績予想の修正に関するお知らせ", EventType.FORECAST_REVISION)
            == Direction.UNKNOWN
        )


class TestFromTdnetDisclosure:
    def test_basic(self) -> None:
        disclosure = {
            "id": "TD001",
            "pubdate": "2026-02-10T15:00:00",
            "company_code": "7203",
            "company_name": "トヨタ自動車株式会社",
            "title": "2026年3月期 第3四半期決算短信",
            "category": "earnings",
            "document_url": "https://example.com/doc.pdf",
        }
        event = from_tdnet_disclosure(disclosure)
        assert event.event_type == EventType.EARNINGS
        assert event.company_ticker == "7203"
        assert event.direction == Direction.UNKNOWN
        assert len(event.sources) == 1
        assert event.sources[0].source.value == "tdnet"

    def test_revision_with_direction(self) -> None:
        disclosure = {
            "id": "TD002",
            "pubdate": "2026-02-15T16:00:00",
            "company_code": "6758",
            "company_name": "ソニーグループ",
            "title": "業績予想の上方修正に関するお知らせ",
            "category": "forecast_revision",
        }
        event = from_tdnet_disclosure(disclosure)
        assert event.event_type == EventType.FORECAST_REVISION
        assert event.direction == Direction.UP

    def test_unknown_category(self) -> None:
        disclosure = {
            "id": "TD003",
            "pubdate": "2026-01-01T09:00:00",
            "company_code": "1234",
            "company_name": "テスト",
            "title": "テスト開示",
            "category": "something_new",
        }
        event = from_tdnet_disclosure(disclosure)
        assert event.event_type == EventType.OTHER


class TestFromEdinetFiling:
    def test_annual_report(self) -> None:
        filing = {
            "doc_id": "S100ABC",
            "edinet_code": "E02144",
            "company_name": "トヨタ自動車株式会社",
            "doc_type": "120",
            "filing_date": "2026-06-25",
            "period_end": "2026-03-31",
            "description": "有価証券報告書",
        }
        event = from_edinet_filing(filing)
        assert event.event_type == EventType.EARNINGS
        assert event.edinet_code == "E02144"
        assert len(event.sources) == 1
        assert event.sources[0].source.value == "edinet"

    def test_extraordinary_report(self) -> None:
        filing = {
            "doc_id": "S100XYZ",
            "edinet_code": "E01777",
            "company_name": "ソニーグループ",
            "doc_type": "180",
            "filing_date": "2026-03-01",
            "description": "臨時報告書",
        }
        event = from_edinet_filing(filing)
        assert event.event_type == EventType.OTHER
