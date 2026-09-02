# Broken Perps fixed-point pricing

Kalshi money/price fields are fixed-point **strings** (up to 4 decimal places),
already in dollars. Parsing with `float` and dividing by 100 silently
underprices by 100x.

## broken.py

Run the checker:

```bash
python ../../scripts/kalshi_doctor.py broken.py
```

```text
kalshi_doctor — scanning /Users/.../kalshi-api-engineering/examples/perps-fixed-point/broken.py
============================================================

  [FAIL] KALSHI-PRICE-001  broken.py:2
         Fixed-point prices are already 4-decimal strings; dividing by 100 underprices 100x.
         found: price = float(price_dollars) / 100  # BUG => 0.0056 (100x too small)
         fix:   Parse Decimal(price_dollars) verbatim; do NOT divide by 100.

  [WARN] KALSHI-PRICE-002  broken.py:2
         Parsing money/price via float() loses decimal precision; use Decimal.

============================================================
  1 FAIL, 1 WARN across 2 finding(s).
```

## fixed.py

Use `Decimal` to preserve the fixed-point value exactly.

Source: https://docs.kalshi.com/perps_openapi.yaml
