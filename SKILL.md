---
name: kalshi-api-engineering
description: "Kalshi API Engineering — Build, debug, and verify Kalshi integrations (Trade API, REST, WebSocket, FIX, Predictions, Perps/Margin). Covers authentication, market data, order entry, order groups, lifecycle handling, execution errors, and production-safe integration patterns."
version: 0.1.0
author: Blake Marcus
license: MIT
homepage: https://github.com/blakee-marcus/kalshi-api-engineering
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Kalshi, KalshiAPI, PredictionMarkets, Perps, Margin, REST, WebSocket, FIX, TradingAPI, AgentSkill]
---

# Kalshi API Engineering

An **engineering / integration reference** for building clients against Kalshi's APIs
— Trade API, REST, WebSocket, FIX, Predictions (event contracts), and Perps / Margin
(perpetual futures). It documents how Kalshi's APIs actually behave and how to build
exchange-safe clients against them.

It is **not a trading bot** and **not a strategy**. It carries no alpha, no trading
logic, and no authorization to place live orders. Where it describes order-entry or
margin semantics, it describes the *protocol* so a client can be built correctly —
not so the agent will trade.

## What this skill is for

- Correct Kalshi REST / WebSocket / FIX hosts, sessions, auth, and price-banding rules
  (Predictions and Perps / Margin).
- Authenticating to Kalshi (RSA-PSS request signing; margin vs predictions WS handshake).
- Reading market data: order books, snapshots/deltas, trust/staleness handling.
- Placing / amending / canceling orders (REST and FIX) with deterministic request builders.
- Order groups, lifecycle states, funding, reconciliation, and execution-error semantics.
- Debugging integrins: "why is my signed request 401ing?", "why is my orderbook stale?".

## What it explicitly will NOT do

- It will **not** place, amend, or cancel live orders. Any state-changing Kalshi call
  requires explicit, separate user authorization outside this skill.
- It does **not** contain credentials, API keys, or private keys, and it will not ask
  you to paste them.
- It does **not** implement trading strategy, alpha, factor models, or risk gates. Those
  are application concerns; this skill only describes the protocol surface they run on.
- It does **not** read or write any private bot repo, personal notes, chat logs, or
  internal system. All content is derived from public Kalshi documentation.

## Authority order (non-negotiable)

1. Current official Kalshi documentation / published specs (docs.kalshi.com).
2. Observed API behavior when it diverges from the docs.
3. This skill's reference pages.
4. Prior implementations, only when explicitly consulted for validated behavior.

Treat the official OpenAPI / AsyncAPI specs as schema authority. If a reference page
disagrees with a published spec, the spec wins and the page should be corrected.

## When to use

Use this skill for any Kalshi integration or API question:

- "What are Kalshi's REST / WebSocket / FIX hosts, sessions, auth, or price-banding rules?"
- "How do I authenticate to Kalshi?" / "How does margin WS auth differ from predictions WS auth?"
- "How do I subscribe to market data?" / "How do I read the order book correctly?"
- "How do I place / amend / cancel orders?" (REST or FIX — New Order Single, order groups, cancels)
- "What are Kalshi's order-entry, order-group, lifecycle, and execution-error semantics?"
- "How do I handle pauses, lifecycle states, funding, or reconciliation safely?"
- "Debug my Kalshi integration" / "Why is my signed request 401ing?" / "Why is my orderbook stale?"

## Environment resolution

```python
PRODUCTION_REST = "https://external-api.kalshi.com/trade-api/v2"
DEMO_REST       = "https://external-api.demo.kalshi.co/trade-api/v2"
PRODUCTION_WS   = "wss://external-api-ws.kalshi.com/trade-api/ws/v2"
DEMO_WS         = "wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2"

# Perps / Margin namespaces live UNDER the same Trade API root, with /margin:
PRODUCTION_MARGIN_REST = "https://external-api.kalshi.com/trade-api/v2/margin"
PRODUCTION_MARGIN_WS   = "wss://external-api-margin-ws.kalshi.com/trade-api/ws/v2/margin"
```

Credentials are **not** shared between production and demo.

## Authentication — RSA-PSS request signing

- Headers: `KALSHI-ACCESS-KEY`, `KALSHI-ACCESS-TIMESTAMP` (epoch milliseconds),
  `KALSHI-ACCESS-SIGNATURE` (base64).
- Pre-hash message: `timestamp + HTTP_METHOD + path_without_query` (+ body for POST/PUT/DELETE).
- Algorithm: RSA-PSS with SHA-256, `salt_length = DIGEST_LENGTH`.
- Path to sign: from the API root, e.g. `/trade-api/v2/portfolio/balance`.

```python
import time, base64, requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

KEY_ID, PEM_PATH = "YOUR_KEY_ID", "private_key.pem"
REST = "https://external-api.kalshi.com/trade-api/v2"

def sign(method: str, path: str, key_path: str, body: str | None = None) -> dict:
    ts = str(int(time.time() * 1000))
    if not path.startswith("/trade-api/v2"):
        path = f"/trade-api/v2{path}"
    msg = f"{ts}{method}{path.split('?')[0]}"
    if body:
        msg += body
    key = serialization.load_pem_private_key(open(key_path, "rb").read(), password=None)
    sig = key.sign(msg.encode(), padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                  salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    return {"KALSHI-ACCESS-KEY": KEY_ID,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode(),
            "KALSHI-ACCESS-TIMESTAMP": ts}

# READ-ONLY proof: signed GET to an authenticated margin read endpoint.
# Signing over the FULL /margin path is the rule that makes private calls work (no 401).
# GET never changes state. Prefer the demo base (DEMO_REST) for first runs.
r = requests.get(f"{REST}/margin/balance", headers=sign("GET", "/margin/balance", PEM_PATH))
print(r.status_code)  # 200 = signature accepted (body is your margin balance)
```

**The one rule that breaks most integrations:** margin REST requests must be signed over
the **full `/margin` path** (`/trade-api/v2/margin/...`), or every private endpoint
returns `401` while public (unauthenticated) endpoints still return `200` — a misleading
split that looks like "broken creds." Sign `f"/trade-api/v2/margin{path}"`.

## WebSocket auth (at connect time)

Kalshi WS requires RSA-PSS auth **at connect time**, not per message. Use `timestamp +
"GET" + path` where the path is `/trade-api/ws/v2` for Predictions and
`/trade-api/ws/v2/margin` for Perps / Margin. Reusing the Predictions path on margin
silently fails auth.

## Order book (Predictions) — derive asks, never ingest them

Predictions orderbook returns YES bids and NO bids. Asks are **implied**:

```python
yes_ask = 1 - no_bid
no_ask  = 1 - yes_bid
```

Store only native Kalshi fields; derive the rest. Track snapshot sequence/provenance;
mark the book untrusted on sequence gap, stale age, parse failure, or disconnect, and
demand a fresh snapshot before any decision. Deltas are **increments** to level size,
not absolute assignment. Full pattern in `references/canonical-book-pattern.md`.

## Perps / Margin — non-negotiable rules

- Use the **MARGIN** namespaces (`/trade-api/v2/margin`, `/trade-api/ws/v2/margin`). Never
  reuse Predictions base URLs with guessed paths.
- Perps book = native `bids` / `asks` arrays of `[price, quantity]`; fixed-point dollar
  prices (string, up to 4 dp) and contract counts (string). **No** YES/NO vocabulary,
  **no** complement-derived asks, **no** cent pricing.
- Order `side` is `bid` / `ask`. Create requires `ticker`, `client_order_id`, `side`,
  `count`, `price`, `time_in_force`, `self_trade_prevention_type`. TIF ∈
  `{fill_or_kill, good_till_canceled, immediate_or_cancel}`. STP ∈ `{taker_at_cross, maker}`.
- `reduce_only` is valid **only** with `immediate_or_cancel` or `fill_or_kill`; the margin
  API rejects it otherwise. Enforce in the builder before any request is sent.
- Margin WS has **no** `market_positions` / `market_lifecycle_v2` channels. Do not gate
  trading on their absence. Position/account authority = margin REST
  (`/positions`, `/balance`, `/risk`) + private `user_orders` / `fill` streams.
- Funding estimate is **not** finalized until `next_funding_time`; preserve
  `computed_time` + `next_funding_time`, never infer a finalized payment from the estimate.

Full connectivity catalog (REST/WS/FIX hosts, session types, price banding, FIX auth,
order entry, order groups, error codes) lives in `references/perps-api-connectivity.md`.

## Fixed-point representation

| Suffix | Type | Decimals | Example |
|--------|------|----------|---------|
| `*_dollars` | Price | 4 | `"0.5600"` |
| `*_fp` | Quantity | 2 | `"10.00"` |

Always parse as `Decimal` from string. Never use binary floats for money.

## Pitfalls (verified, source-backed)

- **Never trust summary transcriptions of derived values.** If you report
  `no_bid=0.3000 → yes_ask=0.6900`, verify `1 - 0.3000 = 0.7000`; a typo in a summary is
  not proof the invariant holds. Inspect the exact book state that produced the number.
- **`orderbook_fp` price parsing:** `price_dollars` is already a 4-decimal string. Parse as
  `Decimal(price_dollars)` directly — **do not divide by 100** (silently makes prices 100×
  too small; the bug often hides until a live market is queried).
- **Deltas are increments**, not absolute sets: `levels[price] = levels.get(price, 0) + delta`
  (pop on 0).
- **Margin WS auth path ≠ Predictions path** (see WebSocket auth above).
- **Margin REST signing must cover `/margin`** or every private endpoint 401s.
- **Perps has no predictions lifecycle channels** — don't build the trading gate around
  `market_lifecycle_v2` / `market_positions` (they don't exist on margin WS).
- **WS market-data traffic is not a lifecycle event.** A `ticker` / `orderbook_delta`
  proves the feed is alive but must not refresh lifecycle-state freshness or override a
  non-tradable status.
- **FIX enums:** write prose tables as `New<0>`, `Canceled<4>`; show wire notation as
  `39=0`, `150=F` in code. Do not preserve HTML/JSON escape artifacts (`\u003c`) as wire values.
- **Reproduce published wire examples verbatim.** Do not rewrite `9=150` as `9=000` or
  "illustrative placeholder." If a framing tag must be computed by a real engine, add a
  separate implementation note instead of mutating the quoted example.
- **Attribute a mechanism to the page that documents it.** A protocol-specific page may
  mention a mechanism only as an edge case; the underlying behavior often lives in a linked
  shared overview. Fetch and cite that overview; keep the protocol file scoped to what it
  supports.

## Procedure (build a safe client)

1. **Contract spec first.** One frozen spec for tick, position limits, settlement window.
   No hardcoded values downstream.
2. **Order book (bottom layer).** Native fields only; derive asks; track provenance; trust
   state with fail-closed staleness/sequence handling. See `canonical-book-pattern.md`.
3. **Gates, in order (non-negotiable):**
   ```
   intent → lifecycle gate → exposure guard → order manager → execution adapter
   ```
   - **Lifecycle gate** answers "is this market currently tradable?" Blocks on
     `initialized`, `inactive`, `closed`, `determined`, `disputed`, `amended`, `finalized`;
     fail-closed (`INDETERMINATE`) on missing/stale/untrusted/unknown/contradictory state.
   - **Exposure guard** projects exposure = position + resting orders + proposed fill;
     fail-closed when portfolio state is incomplete; allows reducing/opposite-side orders.
   - **Order manager** validates create/cancel/amend/decrease locally; returns a
     deterministic command; requires and preserves `client_order_id`; enforces tick
     alignment; classifies rate-limit exhaustion separately from transport/auth failures;
     fails closed on unknown `order_id` or terminal status.
   - **Execution adapter** submits only after all gates pass **and** an explicit
     `write_enabled` flag is true.
4. **Trust/staleness** for every feed: snapshot → trusted → valid delta → trusted; gap /
   malformed / disconnect → untrusted → fresh snapshot required.
5. **Boundary tests** for every gate module before claiming done.

## Reference files

- `references/api-documentation-index.md` — what this skill covers, official sources, scope.
- `references/source-manifest.md` — provenance record: each page's official source + ingest date.
- `references/canonical-book-pattern.md` — Predictions book semantics, derive-asks invariant, trust state.
- `references/forecast-percentile-api.md` — Predictions forecast-percentile endpoint.
- `references/historical-candlesticks-api.md` — Predictions historical candlesticks.
- `references/client-trades-api.md` — Predictions client/market trades.
- `references/perps-api-connectivity.md` — Perps/Margin REST + WS + FIX connectivity, price
  banding, auth, order entry, order groups, FIX error codes (single owner for that surface).

## Verification

This skill is documentation + reference. It ships no executable test suite; verify a client
against the demo environment (read-only) before any live call:

- Demo REST/WS bases resolve; credential source exists (never print it).
- Signed request returns `200` on a private endpoint (proves the `/margin` signing rule).
- Orderbook snapshot → trusted; live deltas apply in sequence; `is_decision_quality()` True.
- REST orderbook reconciles with WS book (allow for deltas between calls).
- Reconnect → untrusted → fresh snapshot → trusted (old state never reused as trusted).

## License

MIT — see [LICENSE](LICENSE).
