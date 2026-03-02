"""Event deduplication engine.

Merges events from different sources (TDNET + EDINET) that refer
to the same corporate event. Uses deterministic scoring to decide
whether two events should be merged.
"""

from __future__ import annotations

from japan_finance_events._models import Event, SourceRef

_MERGE_THRESHOLD = 0.75


def dedupe_score(a: Event, b: Event) -> float:
    """Score how likely two events refer to the same corporate event.

    Returns a score between 0.0 and 1.0.
    """
    score = 0.0

    # Same company (by ticker or EDINET code)
    same_ticker = a.company_ticker and a.company_ticker == b.company_ticker
    same_edinet = a.edinet_code and a.edinet_code == b.edinet_code
    if same_ticker or same_edinet:
        score += 0.35

    # Same event type
    if a.event_type == b.event_type:
        score += 0.25

    # Same fiscal period
    if a.fiscal_period_end is not None and a.fiscal_period_end == b.fiscal_period_end:
        score += 0.20

    # Close publication dates (within 48 hours)
    delta_seconds = abs((a.pit_published_at - b.pit_published_at).total_seconds())
    if delta_seconds <= 48 * 3600:
        score += 0.20

    return min(score, 1.0)


def merge_events(primary: Event, secondary: Event) -> Event:
    """Merge two events into one, keeping the earliest PIT timestamp.

    The primary event's fields take precedence. Source references
    from both events are combined.
    """
    pit = min(primary.pit_published_at, secondary.pit_published_at)
    combined_sources: list[SourceRef] = list(primary.sources)
    for src in secondary.sources:
        if src not in combined_sources:
            combined_sources.append(src)

    # Prefer primary's fields, fill gaps from secondary
    return Event(
        event_id=primary.event_id,
        event_type=primary.event_type,
        direction=(
            primary.direction if primary.direction.value != "unknown" else secondary.direction
        ),
        company_ticker=primary.company_ticker or secondary.company_ticker,
        edinet_code=primary.edinet_code or secondary.edinet_code,
        company_name=primary.company_name or secondary.company_name,
        pit_published_at=pit,
        fiscal_period_end=primary.fiscal_period_end or secondary.fiscal_period_end,
        event_date=primary.event_date or secondary.event_date,
        title=primary.title,
        attributes={**secondary.attributes, **primary.attributes},
        sources=combined_sources,
    )


def deduplicate(events: list[Event], *, threshold: float = _MERGE_THRESHOLD) -> list[Event]:
    """Deduplicate a list of events by merging likely duplicates.

    Events with a dedupe_score >= threshold are merged.
    Returns deduplicated list sorted by pit_published_at.
    """
    if not events:
        return []

    result: list[Event] = []
    merged_indices: set[int] = set()

    for i, event_a in enumerate(events):
        if i in merged_indices:
            continue
        current = event_a
        for j in range(i + 1, len(events)):
            if j in merged_indices:
                continue
            event_b = events[j]
            if dedupe_score(current, event_b) >= threshold:
                current = merge_events(current, event_b)
                merged_indices.add(j)
        result.append(current)

    result.sort(key=lambda e: e.pit_published_at)
    return result
