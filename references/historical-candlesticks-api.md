# Kalshi Client Historical Candlesticks API

Official source: https://docs.kalshi.com/api-reference/historical/get-historical-market-candlesticks
Last ingested: 2026-08-28
Scope: Claims supported by the page listed above (historical market candlesticks endpoint).

Documents the Kalshi V2 historical market candlesticks endpoint.

## Method

### `get_historical_market_candlesticks`

```python
def get_historical_market_candlesticks(
    self,
    ticker: str,
    *,
    start_ts: int,
    end_ts: int,
    period_interval: int = 1,
) -> JsonObject:
```

- **Endpoint:** `GET /historical/markets/{ticker}/candlesticks`
- **Returns:** OHLCV data for markets older than the historical cutoff (`market_settled_ts`)
- **Use for:** Backtesting volatility, regime analysis, settlement price verification, historical volume/open interest profiling

## Parameters

| Param | Type | Description |
|-------|------|-------------|
| `ticker` | str | Market ticker (required, e.g., `KXBTC15M-240823T1500`) |
| `start_ts` | int | Unix timestamp (seconds), candlesticks ending on or after this time |
| `end_ts` | int | Unix timestamp (seconds), candlesticks ending on or before this time |
| `period_interval` | int | 1 (1 minute), 60 (1 hour), 1440 (1 day) |

## Response Shape

```json
{
  "ticker": "string",
  "candlesticks": [
    {
      "end_period_ts": 123,
      "yes_bid": {"open": "0.5600", "low": "0.5600", "high": "0.5600", "close": "0.5600"},
      "yes_ask": {"open": "0.5600", "low": "0.5600", "high": "0.5600", "close": "0.5600"},
      "price": {"open": "0.5600", "low": "0.5600", "high": "0.5600", "close": "0.5600", "mean": "0.5600", "previous": "0.5600"},
      "volume": "10.00",
      "open_interest": "10.00"
    }
  ]
}
```

## Integration Notes

- Only works for **settled markets** older than the historical cutoff. Active markets use the live `/markets/candlesticks` endpoint (already implemented as `get_market_candlesticks`).
- The `price` field provides mean/previous which are useful for realized volatility computation.
- `yes_bid`/`yes_ask` OHLC allows reconstructing historical orderbook snapshots.
- Period interval must be 1, 60, or 1440 — validated client-side before request.

## Related Files

- `src/lean/client.py` — implementation (lines ~554-585)
- Kalshi API docs: https://docs.kalshi.com/api-reference/historical/get-historical-market-candlesticks