# Kalshi Client Trade History API

Official source: https://docs.kalshi.com/api-reference/market/get-trades (live), https://docs.kalshi.com/api-reference/historical/get-historical-trades (historical)
Last ingested: 2026-08-28
Scope: Claims supported by the pages listed above (client/market trade history endpoints).

Documents the Kalshi V2 trade history endpoints (live and historical).

## Methods

### `get_market_trades` (live endpoint)
```python
def get_market_trades(
    self,
    *,
    ticker: str | None = None,
    min_ts: int | None = None,
    max_ts: int | None = None,
    limit: int = 100,
    cursor: str | None = None,
    is_block_trade: bool | None = None,
) -> JsonObject:
```
- **Endpoint:** `GET /markets/trades`
- **Returns:** Trades newer than the historical cutoff (`trades_created_ts`)
- **Use for:** Real-time OBI, volume analysis, recent fill price verification, live market microstructure

### `get_historical_trades` (historical endpoint)
```python
def get_historical_trades(
    self,
    *,
    ticker: str | None = None,
    min_ts: int | None = None,
    max_ts: int | None = None,
    limit: int = 100,
    cursor: str | None = None,
    is_block_trade: bool | None = None,
) -> JsonObject:
```
- **Endpoint:** `GET /historical/trades`
- **Returns:** Trades older than the historical cutoff
- **Use for:** Backtesting, regime analysis, long-horizon volume profiling, settlement audit

## Parameters

| Param | Type | Description |
|-------|------|-------------|
| `ticker` | str | Filter to single market (e.g., `KXBTC15M-240823T1500`) |
| `min_ts` | int | Unix timestamp (seconds), filter trades after this time |
| `max_ts` | int | Unix timestamp (seconds), filter trades before this time |
| `limit` | int | Page size, default 100, max 1000 |
| `cursor` | str | Pagination cursor from previous response |
| `is_block_trade` | bool | `true` = only block trades, `false` = only non-block, omit = all |

## Response Shape

```json
{
  "trades": [
    {
      "trade_id": "string",
      "ticker": "string",
      "count_fp": "10.00",
      "yes_price_dollars": "0.5600",
      "no_price_dollars": "0.5600",
      "taker_outcome_side": "yes",
      "taker_book_side": "bid",
      "created_time": "2023-11-07T05:31:56Z",
      "is_block_trade": true,
      "taker_side": "yes"
    }
  ],
  "cursor": "string"
}
```

## Integration Notes

- The live endpoint (`/markets/trades`) is what the bot should use for recent trade flow analysis (OBI, aggressive volume, taker side imbalance).
- The historical endpoint (`/historical/trades`) is for backfill and research — settled markets only.
- Kalshi's cutoff timestamp (`trades_created_ts`) determines which endpoint returns a given trade. Do not assume live endpoint has full history.
- Both endpoints support pagination via `cursor` — iterate until cursor is empty/absent for full results.

## Related Files

- `src/lean/client.py` — implementation (lines ~496-552)
- Kalshi API docs: https://docs.kalshi.com/api-reference/market/get-trades (live), https://docs.kalshi.com/api-reference/historical/get-historical-trades (historical)
- Docs page: https://docs.kalshi.com/getting_started/historical_data (cutoff semantics)