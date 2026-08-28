# Broken WebSocket trust after a sequence gap

A WebSocket orderbook streams snapshots (full book) and deltas (increments). If a
delta sequence number is skipped, the book is internally inconsistent. A client
that keeps trading on it is acting on corrupted state. Correct behavior: mark the
book UNTRUSTED and demand a fresh snapshot.

## broken.py
```python
book = {"trusted": True, "levels": {}}

def on_seq_gap(gap):
    print(f"gap {gap}")   # BUG: logs the gap but keeps trading on a broken book
    continue_trading()
```

Run the checker:
```bash
python ../../scripts/kalshi_doctor.py broken.py
# [WARN] KALSHI-WS-003  broken.py:4
#        A sequence gap must invalidate book trust and force a fresh snapshot.
```

## fixed.py
```python
book = {"trusted": False, "levels": {}}

def on_seq_gap(gap):
    book["trusted"] = False   # FIX: invalidate trust
    resnapshot()              # demand a fresh snapshot before any decision
```

Source: https://docs.kalshi.com/perps_asyncapi.yaml
