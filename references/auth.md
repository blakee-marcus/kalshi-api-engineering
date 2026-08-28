# auth

> Official source: https://docs.kalshi.com/perps_openapi.yaml
> Last ingested: 2026-08-28
> Scope: RSA-PSS request signing and margin vs predictions auth paths.

Diagnose Kalshi request signing, environment, and credential-source problems.

## When to use
- "Private endpoints return 401 but public ones work." (the classic margin trap)
- "Is my RSA-PSS signing correct?"

## The one rule that breaks most integrations
Margin REST requests must be signed over the **full `/margin` path**
(`/trade-api/v2/margin/...`). Omit it and every private endpoint returns `401`
while public (unauthenticated) endpoints still return `200` — a misleading split
that looks like "broken creds."

```python
def sign(method, path, key_path, body=None):
    ts = str(int(time.time() * 1000))
    if not path.startswith("/trade-api/v2"):
        path = f"/trade-api/v2{path}"
    msg = f"{ts}{method}{path.split('?')[0]}"   # path includes /margin for margin calls
    if body: msg += body
    ...  # RSA-PSS SHA-256, salt_length = DIGEST_LENGTH
```

## Symptoms → cause
| Symptom | Likely cause | Rule |
|---------|--------------|------|
| Public 200, private 401 | signing path drops `/margin` | `KALSHI-AUTH-001` |
| `401` on every signed call | wrong key id / clock skew | — |
| WS connects but no private stream | predictions WS path reused for margin | `KALSHI-WS-001` |

## Read-only proof
Sign and `GET` an authenticated read endpoint (demo base first):
```python
r = requests.get(f"{DEMO_REST}/margin/balance", headers=sign("GET", "/margin/balance", PEM_PATH))
print(r.status_code)  # 200 = signature accepted
```
This skill never issues a state-changing call.

## Completion
- The signed read request returns 200 (proves the `/margin` rule) — or the
  failure is explained by key/clock, not the signing path.
