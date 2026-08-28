# audit

> Official source: https://docs.kalshi.com/ (perps_openapi.yaml, perps_asyncapi.yaml)
> Last ingested: 2026-08-28
> Scope: behavioral audit of client code against the rules in `doctor.md`.

Inspect an existing Kalshi integration for the protocol mistakes this skill detects.

## When to use
- "Audit this Kalshi integration."
- A client 401s on private endpoints, misprices, or trades on a stale book.

## Procedure
1. Locate the client code (REST/WS/FIX, predictions or perps/margin).
2. Run the deterministic checker:
   `python scripts/kalshi_doctor.py <path-to-client>`
3. For each FAIL/WARN, route to the matching playbook by rule id:
   - `KALSHI-AUTH-001` → `auth.md`
   - `KALSHI-WS-001` → `perps.md` / `market-data.md`
   - `KALSHI-PRICE-001` / `KALSHI-PRICE-002` → `perps.md`
   - `KALSHI-WS-002/003/004` → `market-data.md`
   - `KALSHI-PERPS-001/002/003` → `perps.md`
   - `KALSHI-ORD-001` → `orders.md`
   - `KALSHI-EXEC-001` → `orders.md` / `source.md`
4. Report PASS/WARN/FAIL with file:line, rule, official source, and suggested fix.
5. Never modify the user's code unless asked.

## Completion
- Every FAIL has a file:line + official source + fix.
- Read-only: no state-changing call issued by the audit itself.
