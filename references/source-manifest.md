# Source Manifest

Official sources:
- Documentation home: https://docs.kalshi.com/
- Machine-readable index: https://docs.kalshi.com/llms.txt
- Predictions REST spec: https://docs.kalshi.com/openapi.yaml
- Predictions WebSocket spec: https://docs.kalshi.com/asyncapi.yaml
- Perps / Margin REST spec: https://docs.kalshi.com/perps_openapi.yaml
- Perps / Margin WebSocket spec: https://docs.kalshi.com/perps_asyncapi.yaml

Last ingested: 2026-08-28
Scope: Provenance record for the reference pages shipped in this skill.

Provenance record for the reference pages shipped in this skill. Every page below
was derived from the official Kalshi documentation linked in
`api-documentation-index.md`.

## Scope statement

Claims in this skill are supported only by the official pages listed per reference.
Nothing here is sourced from a private bot repo, personal notes, chat logs, or
undisclosed internal systems. Pages that once referenced internal project paths or
bots have been scrubbed; if you find a leak, report it and it will be removed.

## Pages

| Reference page | Derived from (official source) | Ingested |
|----------------|-------------------------------|----------|
| `canonical-book-pattern.md` | Predictions orderbook semantics — `openapi.yaml` (`/markets/{ticker}/orderbook`), `asyncapi.yaml` (`orderbook_delta` / `orderbook_snapshot`) | 2026-08-28 |
| `forecast-percentile-api.md` | Predictions REST — forecast percentile endpoint (`openapi.yaml`) | 2026-08-28 |
| `historical-candlesticks-api.md` | Predictions REST — historical candlesticks (`openapi.yaml`) | 2026-08-28 |
| `client-trades-api.md` | Predictions REST — client/market trades (`openapi.yaml`) | 2026-08-28 |
| `perps-api-connectivity.md` | Perps / Margin REST + WebSocket + FIX — `perps_openapi.yaml`, `perps_asyncapi.yaml`, and the perps auth/session/order-entry/order-group doc pages | 2026-08-28 |

## Verification expectations

- Each reference page cites the official source it was derived from (see the
  "Source:" line near the top of the page).
- Cross-cutting mechanisms (lifecycle states, order-group lifecycle, funding) are
  attributed to the page that actually documents them, with links out for
  shared semantics.
- Wire examples from the official docs are reproduced verbatim, not recomputed.
  If a framing tag (e.g. FIX `9=`, `10=`) must be computed by a real engine, that
  is called out as a separate implementation note rather than mutating the quoted
  example.

## Freshness

Last full ingestion pass: **2026-08-28**. Re-verify against the live specs before
relying on a detail for production code. Kalshi's API and specs change; the docs are
the authority.

## Spec hashes (drift baseline)

Short SHA-256 (first 16 hex) of each official spec as last recorded by
`scripts/check_upstream_drift.py`. This block is the committed baseline the
drift monitor compares against on every run — kept in-repo (not a gitignored
sidecar) so a fresh CI checkout can actually detect a change. When a hash
changes, the script rewrites this block; commit it via a PR.

```[spec-hashes]
openapi.yaml=99bdf4093d7eced6
asyncapi.yaml=ff4f5dbcf6c70ecd
perps_openapi.yaml=dee33d2df0b2983a
perps_asyncapi.yaml=8af2212c643e5eff
llms.txt=1bdc65d95f60560b
```
