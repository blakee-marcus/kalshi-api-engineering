# market-data

> Official source: https://docs.kalshi.com/perps_asyncapi.yaml
> Last ingested: 2026-08-28
> Scope: orderbook / WebSocket correctness and trust-state handling.

Orderbook / WebSocket correctness and trust-state review (Predictions + Perps).

## When to use
- "My order book goes stale / prices look wrong."
- "How do I trust the WS feed after a reconnect?"

## Predictions book — derive asks
Predictions orderbook returns YES bids and NO bids. Asks are **implied**:
```python
yes_ask = 1 - no_bid
no_ask  = 1 - yes_bid
```

## Perps book — native arrays
Perps book = native `bids` / `asks` of `[price, quantity]`. `price` is a
fixed-point 4-dp **string** (`"0.5600"`); `quantity` is a string count.
**No** YES/NO vocabulary, **no** complement-derived asks, **no** cent pricing.

## Trust state (non-negotiable)
- Snapshot → `TRUSTED` → valid delta → `TRUSTED`.
- Any of: sequence gap, stale age, parse failure, disconnect → `UNTRUSTED`
  and demand a **fresh snapshot** before any decision. (`KALSHI-WS-003`)
- Deltas are **increments**: `levels[p] = levels.get(p, 0) + delta` (pop on 0).
  Never assign `levels[p] = delta`. (`KALSHI-WS-002`)
- After reconnect: reset to `UNTRUSTED`; old snapshot is never reused as
  trusted. (`KALSHI-WS-004`)
- WS market-data traffic is **not** a lifecycle event. (`KALSHI-WS-...` pitfall)

## Completion
- Book is `TRUSTED` only after a verified fresh snapshot; every delta applied
  as an increment; gaps force re-snapshot.
