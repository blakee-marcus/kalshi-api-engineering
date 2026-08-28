---
name: kalshi-api-engineering
description: "Kalshi API engineering: audit, doctor, and build correct Kalshi integrations (Trade API, REST, WebSocket, FIX, Predictions, Perps/Margin)."
version: 0.2.0
author: Blake Marcus, Hermes Agent
license: MIT
homepage: https://github.com/blakee-marcus/kalshi-api-engineering
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Kalshi, KalshiAPI, PredictionMarkets, Perps, Margin, REST, WebSocket, FIX, TradingAPI, AgentSkill]
---

# Kalshi API Engineering

A source-backed agent skill for building **correct, exchange-safe Kalshi
integrations** — Trade API, REST, WebSocket, FIX, Predictions (event contracts),
and Perps / Margin (perpetual futures). It is documentation + a deterministic
checker, **not a trading bot**: it describes the protocol so a client is built
correctly, and it audits client code for the mistakes LLMs repeatedly make.

## Command vocabulary

Route each request to one playbook:

| Command | Playbook | Use it for |
|---------|----------|------------|
| `audit` | `audit.md` | Inspect an existing integration for protocol mistakes |
| `doctor` | `doctor.md` | Run the deterministic checker (CI gate) |
| `auth` | `auth.md` | Diagnose RSA-PSS signing / 401s |
| `market-data` | `market-data.md` | Orderbook / WS trust-state review |
| `perps` | `perps.md` | Build/debug Perps / Margin integration |
| `orders` | `orders.md` | Order construction, reconciliation, cancels |
| `source` | `source.md` | Resolve a claim against current Kalshi docs/specs |

Run the checker directly:
```bash
python scripts/kalshi_doctor.py <path-to-client>      # PASS/WARN/FAIL report
python scripts/kalshi_doctor.py <path> --json         # machine-readable
```

## What it will NOT do
- It will **not** place, amend, or cancel live orders. Any state-changing Kalshi
  call requires explicit, separate user authorization outside this skill.
- No credentials, API keys, or private keys; it will not ask you to paste them.
- No trading strategy / alpha. It describes the protocol surface only.
- No reads/writes of any private repo, notes, chat logs, or internal system.
- Every example is **read-only** (`GET`); CI fails on embedded state-changing calls.

## Authority order (non-negotiable)
1. Current official Kalshi docs / published specs (docs.kalshi.com).
2. Observed API behavior when it diverges from the docs.
3. This skill's reference pages.
4. Prior implementations, only when explicitly consulted.

Official specs are schema authority. If a reference page disagrees with a
published spec, the spec wins and the page should be corrected (open a
docs-drift issue).

## Connectivity (router-level facts)
- REST root: `https://external-api.kalshi.com/trade-api/v2`
- Demo REST: `https://external-api.demo.kalshi.co/trade-api/v2`
- Margin REST is under the same root with `/margin`: `.../trade-api/v2/margin`
- WS auth path: `/trade-api/ws/v2` (Predictions), `/trade-api/ws/v2/margin` (Perps)
- Auth headers: `KALSHI-ACCESS-KEY`, `KALSHI-ACCESS-TIMESTAMP` (ms),
  `KALSHI-ACCESS-SIGNATURE` (base64). RSA-PSS SHA-256, `salt_length=DIGEST_LENGTH`.
- **One rule:** margin REST/WS requests must be signed over the full `/margin`
  path or every private endpoint 401s while public ones still return 200.

## Read-only signing proof (safe example)
```python
import time, base64, requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

KEY_ID, PEM_PATH = "YOUR_KEY_ID", "private_key.pem"
REST = "https://external-api.demo.kalshi.co/trade-api/v2"   # demo: read-only

def sign(method, path, key_path, body=None):
    ts = str(int(time.time() * 1000))
    if not path.startswith("/trade-api/v2"):
        path = f"/trade-api/v2{path}"
    msg = f"{ts}{method}{path.split('?')[0]}"
    if body: msg += body
    key = serialization.load_pem_private_key(open(key_path, "rb").read(), password=None)
    sig = key.sign(msg.encode(), padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                  salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    return {"KALSHI-ACCESS-KEY": KEY_ID,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode(),
            "KALSHI-ACCESS-TIMESTAMP": ts}

# READ-ONLY: signed GET to an authenticated margin read endpoint. GET never changes state.
r = requests.get(f"{REST}/margin/balance", headers=sign("GET", "/margin/balance", PEM_PATH))
print(r.status_code)  # 200 = signature accepted (body is your demo margin balance)
```

## Procedure (handle a request)
1. Pick the command from the vocabulary above; load its playbook.
2. For `audit`/`doctor`: run `scripts/kalshi_doctor.py <path>`; report each
   FAIL/WARN with file:line, rule id, official source, and fix.
3. For a how-to: answer from the playbook + `references/`; cite the official URL.
4. Verify any claim against the current spec when docs may have drifted (`source.md`).
5. Never issue a state-changing call. If the user wants one, require explicit
   authorization + an execution boundary outside this skill.

## Pitfalls (verified, source-backed)
- Margin signing must cover `/margin` or every private endpoint 401s.
- Predictions WS auth path ≠ Perps WS auth path (silent auth failure).
- `*_dollars` prices are 4-dp strings; `Decimal(...)` — never divide by 100.
- Deltas are increments, not absolute assignment; gaps force re-snapshot.
- Perps WS has no `market_lifecycle_v2` / `market_positions` channels.
- `reduce_only` only with `immediate_or_cancel` / `fill_or_kill`.

## Reference files
- `references/audit.md`, `doctor.md`, `auth.md`, `market-data.md`, `perps.md`,
  `orders.md`, `source.md` — the command playbooks.
- `references/api-documentation-index.md` — what's covered + official sources.
- `references/source-manifest.md` — per-page source URL + ingest date.
- `references/canonical-book-pattern.md`, `forecast-percentile-api.md`,
  `historical-candlesticks-api.md`, `client-trades-api.md`,
  `perps-api-connectivity.md` — endpoint/connectivity detail.

## Verification
- Skill is documentation + a checker; it ships no executable client.
- `python scripts/verify_public_surface.py` — public-surface CI gate.
- `pytest tests/test_kalshi_doctor.py` — every detector rule has a positive +
  negative fixture.
- A client you build should be verified against the **demo** environment first.

## License
MIT — see [LICENSE](LICENSE).
