# Kalshi API Engineering

An agent **skill** (and plain reference) for building correct, exchange-safe clients
against [Kalshi's APIs](https://docs.kalshi.com/) — Trade API, REST, WebSocket, FIX,
Predictions (event contracts), and Perps / Margin (perpetual futures).

> **Engineering reference, not a trading bot.** It documents how Kalshi's APIs behave
> and how to integrate against them. It contains **no trading strategy, no alpha, and no
> authorization to place live orders.** Any state-changing Kalshi call requires explicit,
> separate user authorization outside this skill.

## Why this exists

Most Kalshi integrations fail the same way: the margin REST auth path drops `/margin`,
so every private endpoint returns `401` while public ones still work — a misleading split
that looks like "broken creds." This skill is the curated, source-backed reference for
that gotcha and the full endpoint/connectivity catalog, kept faithful to the official docs.

## What it prevents

- Signed requests that 401 because the `/margin` path was dropped from the signature.
- Order books built from independently-supplied asks (they must be **derived**).
- Fixed-point prices divided by 100 (they're already 4-decimal strings).
- Trusting a stale or gapped book, or reusing pre-reconnect state as trusted.
- Reusing the Predictions WebSocket auth path on the margin WebSocket (silent auth failure).
- Building a trading gate around `market_lifecycle_v2` / `market_positions` (absent on margin WS).
- Treating WS market-data traffic as a lifecycle event (it is not).

## Provenance — where the knowledge came from

Every reference page is derived from the **public Kalshi documentation**, not from a
private bot or personal notes. See `references/api-documentation-index.md` (what's covered,
official sources) and `references/source-manifest.md` (per-page source + ingest date).

| Authority | Source |
|-----------|--------|
| Docs home | https://docs.kalshi.com/ |
| Page index | https://docs.kalshi.com/llms.txt |
| Predictions REST | https://docs.kalshi.com/openapi.yaml |
| Predictions WS | https://docs.kalshi.com/asyncapi.yaml |
| Perps / Margin REST | https://docs.kalshi.com/perps_openapi.yaml |
| Perps / Margin WS | https://docs.kalshi.com/perps_asyncapi.yaml |

**Authority order:** (1) official docs/specs → (2) observed API behavior → (3) this skill's
pages → (4) prior implementations only when explicitly consulted. The published specs are
schema authority.

## Read-only vs state-changing boundaries

| Scope | Allowed by this skill | Requires |
|-------|----------------------|----------|
| Reading public/authenticated market data, specs, docs | Yes (described) | Your own API key |
| Building/signing request payloads locally | Yes (described) | — |
| **Placing / amending / canceling live orders** | **No** | Explicit, separate user authorization |
| Live trading / strategy execution | **No** | Your own application + authorization |

This skill describes the protocol. It never triggers a state-changing call on your behalf.

## Permissions & tools it uses

- **No network calls.** The skill is documentation; it makes no requests.
- **No filesystem writes** outside normal skill installation (copying `SKILL.md` +
  `references/`).
- **No credentials.** It does not read, store, or ask for API keys or private keys.
- A client *you* build from it will need your Kalshi API key + private key to authenticate,
  handled entirely in your code/environment — never in this repo.

## What it will NOT do

- Will not place, amend, or cancel live orders.
- Will not ask you to paste private keys or secrets.
- Will not authorize live trading.
- Will not read or write any private bot repo, personal notes, chat logs, or internal system.

## Coverage / status

| Surface | Reference | Status |
|---------|-----------|--------|
| Predictions — orderbook / canonical-book semantics | `canonical-book-pattern.md` | Ingested 2026-08-28 |
| Predictions — forecast percentile | `forecast-percentile-api.md` | Ingested 2026-08-28 |
| Predictions — historical candlesticks | `historical-candlesticks-api.md` | Ingested 2026-08-28 |
| Predictions — client trades | `client-trades-api.md` | Ingested 2026-08-28 |
| Perps / Margin — REST + WS + FIX connectivity, auth, order entry, order groups, error codes | `perps-api-connectivity.md` | Ingested 2026-08-28 |

Out of scope (read the official specs): full endpoint-by-endpoint REST catalogs beyond the
pages above, account/portfolio read endpoints not summarized in `perps-api-connectivity.md`,
FIX session-replay/certification, and Kalshi Academy tutorials. Claims are scoped to the
pages listed; "authoritative reference bank" is **not** claimed for surfaces not covered.

## Installation

### Primary — skill managers

```bash
npx skills add blakee-marcus/kalshi-api-engineering
```

(If your agent framework uses the Skills registry / a compatible CLI, that is the supported path.)

### Manual — any agent framework

Copy `SKILL.md` and `references/` into your skill directory:

```bash
SKILL_DIR="$HOME/.hermes/skills/trading/kalshi-api-engineering"   # or your framework's path
mkdir -p "$SKILL_DIR/references"
cp SKILL.md "$SKILL_DIR/"
cp -r references/. "$SKILL_DIR/references/"
```

### Maintainer-only sync (not for consumers)

`scripts/maintainer-sync-hermes.sh` is a **maintainer-only** helper that syncs this source
repo into a locally installed Hermes skill copy. Do not run it from a clone you don't
maintain. Its removal of the installed `references/` is intentional and scoped to the
installed copy only.

## Supported runtimes

- Any agent runtime that loads `SKILL.md` + `references/` (Hermes, and others via manual copy).
- Python examples use `cryptography` + `requests` for signing demos; the skill content is
  language-agnostic.

## 30-second start — the one rule

```python
import time, base64, requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

KEY_ID, PEM_PATH = "YOUR_KEY_ID", "private_key.pem"
REST = "https://external-api.kalshi.com/trade-api/v2"

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

# DELETE /margin/orders — Cancel All Orders (204). Pass subaccount to scope; omit to sweep ALL.
# Sign over the FULL /margin path or every private endpoint 401s.
r = requests.delete(f"{REST}/margin/orders", headers=sign("DELETE", "/margin/orders", PEM_PATH))
print(r.status_code)  # 204
```

## Verification methodology

This skill ships **documentation + reference**, not an executable test suite. Verify a client
you build against the **demo environment** (read-only) before any live call:

1. Demo REST/WS bases resolve; credential source exists (never print it).
2. A signed private-endpoint request returns `200` (proves the `/margin` signing rule).
3. Orderbook snapshot → trusted; live deltas apply in sequence; decision-quality True.
4. REST orderbook reconciles with the WS book (allow for deltas between calls).
5. Reconnect → untrusted → fresh snapshot → trusted (old state never reused as trusted).

A CI workflow (`.github/workflows/verify.yml`) checks the public surface on every push:
valid frontmatter, required files present, no personal absolute paths or internal project
paths, no credential material, no broken local reference links, no bot-specific identifiers,
and that every reference page carries a source URL.

## Topics

`kalshi`, `kalshi-api`, `prediction-markets`, `agent-skills`, `fix-protocol`,
`websocket`, `trading-api`, `perps`, `margin`, `algorithmic-trading`, `rsa-pss`

## License

MIT — see [LICENSE](LICENSE). Security policy: [SECURITY.md](SECURITY.md).
