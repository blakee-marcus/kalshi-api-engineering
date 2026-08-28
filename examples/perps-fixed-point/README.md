# Broken Perps fixed-point pricing

Kalshi money/price fields are fixed-point **strings** (up to 4 decimal places),
already in dollars. Parsing with `float` and dividing by 100 silently
underprices by 100x.

## broken.py
```python
price_dollars = "0.5600"
price = float(price_dollars) / 100   # BUG => 0.0056 (100x too small)
```

Run the checker:
```bash
python ../../scripts/kalshi_doctor.py broken.py
# [FAIL] KALSHI-PRICE-001  broken.py:2
#        Fixed-point prices are already 4-decimal strings; dividing by 100 underprices 100x.
```

## fixed.py
```python
from decimal import Decimal
price_dollars = "0.5600"
price = Decimal(price_dollars)   # FIX => Decimal('0.5600')
```

Source: https://docs.kalshi.com/perps_openapi.yaml
