# Kalshi API Documentation Index

This skill's reference material is a curated, source-backed subset of the public
Kalshi API documentation. It is an **engineering reference**, not a trading bot and
not a copy of the full docs.

## Official sources

- Documentation home: https://docs.kalshi.com/
- Machine-readable index (discover all pages): https://docs.kalshi.com/llms.txt
- Predictions REST spec: https://docs.kalshi.com/openapi.yaml
- Predictions WebSocket spec: https://docs.kalshi.com/asyncapi.yaml
- Perps / Margin REST spec: https://docs.kalshi.com/perps_openapi.yaml
- Perps / Margin WebSocket spec: https://docs.kalshi.com/perps_asyncapi.yaml

## What this skill covers

| Surface | Reference page | Base spec |
|---------|---------------|-----------|
| Predictions — orderbook / canonical book semantics | `canonical-book-pattern.md` | `openapi.yaml`, `asyncapi.yaml` |
| Predictions — forecast percentile endpoint | `forecast-percentile-api.md` | `openapi.yaml` |
| Predictions — historical candlesticks | `historical-candlesticks-api.md` | `openapi.yaml` |
| Predictions — client trades | `client-trades-api.md` | `openapi.yaml` |
| Perps / Margin — REST, WebSocket, FIX connectivity, price banding, auth, order entry, order groups, error codes | `perps-api-connectivity.md` | `perps_openapi.yaml`, `perps_asyncapi.yaml` |

## What this skill does NOT cover

This is intentionally scoped. The following are out of scope for the reference set
and should be read from the official specs above when needed:

- Full endpoint-by-endpoint REST catalogs beyond the pages listed (fetch the YAML specs).
- Account/portfolio read endpoints not summarized in `perps-api-connectivity.md`.
- FIX session-replay and certification workflows.
- Kalshi Academy educational/tutorial content (https://help.kalshi.com/).

## Authority order

1. Current official Kalshi documentation / published specs (docs.kalshi.com).
2. Observed API behavior when it diverges from the docs (note the divergence).
3. This skill's reference pages.
4. Prior implementations, only when explicitly consulted.

Treat the official specs as schema authority. Where a reference page and a published
spec disagree, the spec wins and the page should be corrected.

## Last ingested

2026-08-28
