# orders

> Official source: https://docs.kalshi.com/perps_openapi.yaml
> Last ingested: 2026-08-28
> Scope: order construction, reconciliation, cancel semantics, execution boundary.

Review order construction, reconciliation, and cancel semantics.

## When to use
- "Build / validate an order before sending."
- "Why did my cancel not scope right?"

## Construction
- Every create carries a **stable `client_order_id`** for reconciliation and
  idempotency. (`KALSHI-ORD-001`)
- Enforce tick alignment and required fields locally before sending.
- `reduce_only` only with `immediate_or_cancel` / `fill_or_kill` (see `perps.md`).

## Reconciliation
- Match fills to `client_order_id`, not to exchange-assigned `order_id` alone.
- Fail closed on unknown `order_id` or terminal status.

## Cancels
- `DELETE /margin/orders` cancels **all** matching resting orders; pass
  `subaccount` to scope. This is destructive — never issue it without explicit
  user authorization.
- The skill describes the endpoint; it never calls it.

## Execution boundary (safety)
Any state-changing call (`POST`/`PUT`/`PATCH`/`DELETE`) must sit behind an
explicit, user-authorized `write_enabled` flag. (`KALSHI-EXEC-001`)
The skill's own examples are read-only (`GET`).

## Completion
- Order validated locally (fields, tick, reduce_only TIF) before send.
- State-changing calls gated behind an explicit write boundary.
