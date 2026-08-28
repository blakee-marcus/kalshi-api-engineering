# doctor

> Official source: https://docs.kalshi.com/ (perps_openapi.yaml, perps_asyncapi.yaml)
> Last ingested: 2026-08-28
> Scope: the deterministic checker engine and its rule catalog.

Deterministic environment/config/client diagnosis. The engine is
`scripts/kalshi_doctor.py`; this playbook explains how to run and read it.

## When to use
- "Run the doctor on my Kalshi client."
- Before shipping an integration; in CI as a gate.

## How to run
```bash
python scripts/kalshi_doctor.py .            # scan a directory
python scripts/kalshi_doctor.py client.py    # one file
python scripts/kalshi_doctor.py . --json     # machine-readable
```

## Output
```
[FAIL] KALSHI-AUTH-001  path:line
       why
       found: <snippet>
       fix:   <suggested fix>
       src:   https://docs.kalshi.com/ (openapi.yaml, perps_openapi.yaml, ...)
```
Exit code 0 = no FAIL; 1 = at least one FAIL (CI can gate on it).

## Rules (stable ids)
| Rule | Severity | What it catches |
|------|----------|-----------------|
| `KALSHI-AUTH-001` | FAIL | Margin signing omits `/margin` |
| `KALSHI-WS-001` | FAIL | Predictions WS auth path reused for Perps |
| `KALSHI-PRICE-001` | FAIL | `*_dollars` divided by 100 |
| `KALSHI-PRICE-002` | WARN | Binary float for Kalshi money/price |
| `KALSHI-WS-002` | FAIL | Orderbook delta treated as absolute |
| `KALSHI-WS-003` | WARN | Sequence gap does not invalidate trust |
| `KALSHI-WS-004` | WARN | Reconnect reuses old snapshot as trusted |
| `KALSHI-PERPS-001` | FAIL | Perps expects `market_lifecycle_v2` |
| `KALSHI-PERPS-002` | FAIL | Perps expects `market_positions` |
| `KALSHI-PERPS-003` | FAIL | `reduce_only=true` + GTC |
| `KALSHI-ORD-001` | WARN | Order create lacks `client_order_id` |
| `KALSHI-EXEC-001` | FAIL | State-changing call without execution boundary |

## Adding a rule
1. Reproduce the bug in `tests/fixtures/bad/`.
2. Add the matching positive fix in `tests/fixtures/good/`.
3. Implement the detector in `scripts/kalshi_doctor.py` with a `KALSHI-XXX-NNN` id.
4. Add positive + negative assertions in `tests/test_kalshi_doctor.py`.

## Completion
- The run exits 0 on clean code, 1 on any FAIL.
- Every rule has a passing positive + negative fixture.
