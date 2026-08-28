# perps

> Official source: https://docs.kalshi.com/perps_openapi.yaml
> Last ingested: 2026-08-28
> Scope: Perps / Margin REST + WS + FIX connectivity, auth, pricing, order entry.

Build or debug a Perps / Margin (perpetual futures) Kalshi integration.

## When to use
- "Wire up Perps REST + WebSocket + FIX."
- "My Perps client 401s / misprices / expects missing channels."

## Namespaces
- REST root: `https://external-api.kalshi.com/trade-api/v2/margin`
- WS auth path: `/trade-api/ws/v2/margin` (NOT the predictions path)
- Sign over the full `/margin` path or every private call 401s.

## Pricing
- `price_dollars` is a 4-decimal string. `Decimal(price_dollars)` — **do not**
  divide by 100. (`KALSHI-PRICE-001`)
- Use `Decimal` for all money; never binary `float`. (`KALSHI-PRICE-002`)

## Order create
- Required: `ticker`, `client_order_id`, `side`, `count`, `price`,
  `time_in_force`, `self_trade_prevention_type`.
- `side` ∈ `bid` / `ask`. TIF ∈
  `{fill_or_kill, good_till_canceled, immediate_or_cancel}`.
- `reduce_only` valid **only** with `immediate_or_cancel` or `fill_or_kill`.
  GTC + reduce_only is rejected. (`KALSHI-PERPS-003`)

## Channels that do NOT exist on margin WS
- `market_lifecycle_v2` — absent. (`KALSHI-PERPS-001`)
- `market_positions` — absent. (`KALSHI-PERPS-002`)
- Use margin REST (`/positions`, `/balance`, `/risk`) + private `user_orders`
  / `fill` streams for position/account state.

## Completion
- Perps endpoints use `/margin` consistently; prices are Decimal; no absent
  channels referenced; `reduce_only` only with IOC/FOK.
