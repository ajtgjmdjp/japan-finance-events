# japan-finance-events

Event-driven corporate event dataset for Japanese financial data with Point-in-time (PIT) support.

## Features

- Canonical event model with PIT timestamps (prevents lookahead bias)
- TDNET and EDINET normalizers
- Rule-based direction classification (upward/downward revision, dividend increase/decrease)
- Cross-source deduplication engine
- PIT-aware query API

## Installation

```bash
pip install japan-finance-events
```

## License

Apache-2.0
