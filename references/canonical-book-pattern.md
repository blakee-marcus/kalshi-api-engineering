# Canonical Book Pattern — Design Detail

Official source: https://docs.kalshi.com/openapi.yaml (orderbook), https://docs.kalshi.com/asyncapi.yaml (orderbook_delta / orderbook_snapshot)
Last ingested: 2026-08-28
Scope: Claims supported by the specs listed above (Predictions orderbook semantics).

## Core Invariant

Kalshi's Predictions orderbook returns YES bids and NO bids. Asks are *implied*:

```
yes_ask = 1 - no_bid
no_ask  = 1 - yes_bid
```

Never ingest an independently supplied ask. Derive it from the opposite-side bid. This matches the exchange rather than fighting it.

## CanonicalBookState Design

### Stored (native Kalshi only)
- `yes_levels: list[BookLevel]` — (price, size) where price is YES bid
- `no_levels: list[BookLevel]` — (price, size) where price is NO bid
- `snapshot_provenance: SnapshotProvenance | None`

### Derived (never stored)
- `best_yes_bid()` → highest YES bid with size > 0
- `best_no_bid()` → highest NO bid with size > 0
- `derived_yes_ask()` → `Decimal("1") - best_no_bid()`
- `derived_no_ask()` → `Decimal("1") - best_yes_bid()`
- `executable_spread()` → `derived_yes_ask() - best_yes_bid()`

### Provenance
```python
@dataclass(frozen=True)
class SnapshotProvenance:
    source: str                    # "ws_snapshot", "ws_delta", "rest_fallback"
    sequence: int
    received_monotonic_ns: int
    received_wall_iso: str
    is_gapped: bool = False
    gap_size: int = 0
```

### Trust State
- `is_trusted=False` when: sequence gap > `max_gap_tolerance` (default 5) OR age > `max_book_age_seconds` (default 3.0)
- `is_usable()` = has_snapshot AND is_trusted AND best_yes_bid AND derived_yes_ask AND age ≤ max

## Critical Bug: Staleness Check Order

**WRONG** (marks every snapshot stale):
```python
elif self._compute_book_age() > self.max_book_age_seconds:  # uses OLD last_delta_received_monotonic_ns=0 → inf
    is_trusted = False
return replace(self, ... last_delta_received_monotonic_ns=received_monotonic_ns ...)
```

**RIGHT** (check AFTER replace):
```python
new_book = replace(self, ... last_delta_received_monotonic_ns=received_monotonic_ns ...)
if new_book._compute_book_age() > self.max_book_age_seconds:
    new_book = replace(new_book, is_trusted=False, untrusted_reason="stale")
return new_book
```

## Regression Test Anatomy

```python
def test_normalization_regression():
    book = CanonicalBookState(ticker="KXBTC15M-TEST")
    # Complementary: YES bid 0.994 + NO bid 0.006
    book = replace(book,
        yes_levels=[BookLevel(price=Decimal("0.994"), size=Decimal("100"))],
        no_levels=[BookLevel(price=Decimal("0.006"), size=Decimal("100"))],
        has_snapshot=True, is_trusted=True)
    assert book.derived_yes_ask() == Decimal("0.994")
    assert book.derived_no_ask() == Decimal("0.006")
    # Must NOT have mutable yes_ask field
    assert not hasattr(book, "yes_ask")
    # Complementarity clean
    assert len(book.validate_complementarity()) == 0
```

**Bug case from production:** external `yes_ask=0.988` with `no_bid=0.006` is forbidden. Canonical derives `yes_ask=0.994`. The mismatch is a normalization defect, NOT arbitrage.

## Acceptance Bar (Phase 1)

- [x] one authoritative BookState exists
- [x] asks always derived from opposite bids
- [x] every executable quote has provenance
- [x] stale/gapped books become untrusted
- [x] REST/WS mixed-source cannot silently merge
- [x] tick normalization at boundary (`parse_fp` + `CONTRACT_SPEC.round_to_tick`)
- [x] replay reproduces deterministically
- [x] existing bot runs behind flag
- [x] old vs new divergences logged
- [x] normalization regression case passes
