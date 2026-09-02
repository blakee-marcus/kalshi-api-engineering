# Broken authentication — the classic margin 401 trap

Public endpoints return `200`; private endpoints return `401`. The developer
concludes "bad credentials." The real cause: the margin REST request is signed
over `/trade-api/v2/...` but the margin path segment `/margin` was dropped from
the signed message, so Kalshi rejects the signature on every private call.

## broken.py

Run the checker:

```bash
python ../../scripts/kalshi_doctor.py broken.py
```

```text
kalshi_doctor — scanning /Users/.../kalshi-api-engineering/examples/auth-401/broken.py
============================================================

  [FAIL] KALSHI-AUTH-001  broken.py:5
         Margin request signing must cover the full /trade-api/v2/margin/... path.
         found: sign(
         fix:   Sign the full /trade-api/v2/margin/... path for every margin REST request.
         src:   https://docs.kalshi.com/ (...)

============================================================
  1 FAIL, 0 WARN across 1 finding(s).
```

## fixed.py

The signer now ensures every margin call is signed over the full
`/trade-api/v2/margin/...` path.

Source: https://docs.kalshi.com/perps_openapi.yaml
