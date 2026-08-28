# Kalshi Client Event Forecast Percentile History API

Official source: https://docs.kalshi.com/api-reference/events/get-event-forecast-percentile-history
Last ingested: 2026-08-28
Scope: Claims supported by the page listed above (event forecast percentile history endpoint).

Documents the Kalshi V2 event forecast percentile history endpoint.

## Method

### `get_event_forecast_percentile_history`

```python
def get_event_forecast_percentile_history(
    self,
    series_ticker: str,
    event_ticker: str,
    *,
    percentiles: list[int],
    start_ts: int,
    end_ts: int,
    period_interval: int = 1,
) -> JsonObject:
```

- **Endpoint:** `GET /series/{series_ticker}/events/{event_ticker}/forecast_percentile_history`
- **Returns:** Market's forecast distribution over time (percentile points at each period)
- **Use for:** Market-implied volatility from the exchange's own model, regime classification, calibration targets, historical probability calibration

## Parameters

| Param | Type | Description |
|-------|------|-------------|
| `series_ticker` | str | Series (e.g., `KXBTC15M`) |
| `event_ticker` | str | Event (e.g., `KXBTC15M-240823T1500`) |
| `percentiles` | list[int] | 1-10 percentile values (0-9999, e.g., `[10, 25, 50, 75, 90]`) |
| `start_ts` | int | Unix timestamp (seconds), start of range |
| `end_ts` | int | Unix timestamp (seconds), end of range |
| `period_interval` | int | 0 (5-second), 1 (1 min), 60 (1 hour), 1440 (1 day) |

## Response Shape

```json
{
  "forecast_history": [
    {
      "event_ticker": "string",
      "end_period_ts": 123,
      "period_interval": 123,
      "percentile_points": [
        {
          "percentile": 123,
          "raw_numerical_forecast": 123,
          "numerical_forecast": 123,
          "formatted_forecast": "string"
        }
      ]
    }
  ]
}
```

## Integration Notes

- This endpoint provides the **market's own forecast distribution** — not the bot's model. Useful for:
  - Computing market-implied volatility from percentiles (e.g., 10th-90th spread)
  - Regime classification using the exchange's model
  - Calibration: comparing bot's probability to market's forecast distribution
  - Historical analysis without maintaining local BRTI observation buffers
- Requires authentication (API key + RSA-PSS signature)
- Max 10 percentiles per request; percentiles in range 0-9999 (basis points)
- Period interval 0 = 5-second granularity (highest resolution)

## Related Files

- `src/lean/client.py` — implementation (lines ~587-625)
- Kalshi API docs: https://docs.kalshi.com/api-reference/events/get-event-forecast-percentile-history