# Broken WebSocket trust after a sequence gap

A WebSocket orderbook streams snapshots (full book) and deltas (increments). If a
delta sequence number is skipped, the book is internally inconsistent. A client
that keeps trading on it is acting on corrupted state. Correct behavior: mark the
book UNTRUSTED and demand a fresh snapshot.

## broken.py

Run the checker:

```bash
python ../../scripts/kalshi_doctor.py broken.py
```

```text
kalshi_doctor — scanning /Users/.../kalshi-api-engineering/examples/ws-sequence-gap/broken.py
============================================================

  [WARN] KALSHI-WS-003  broken.py:3
         A sequence gap must invalidate book trust and force a fresh snapshot.
         found: gap
         fix:   On any sequence gap, mark the book UNTRUSTED and demand a fresh snapshot.

============================================================
  0 FAIL, 1 WARN across 1 finding(s).
```

## fixed.py

The gap handler invalidates trust and resnapshots before any decision.

Source: https://docs.kalshi.com/perps_asyncapi.yaml
