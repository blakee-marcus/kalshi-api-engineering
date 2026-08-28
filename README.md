# Kalshi API Engineering

**Make your AI coding agent reliable at Kalshi.**

Source-backed REST, WebSocket, FIX and Perps guidance — plus a deterministic
checker that catches the integration bugs LLMs repeatedly generate.

```bash
npx skills add blakee-marcus/kalshi-api-engineering
```

Then ask your agent:

> **Audit this Kalshi integration.**

[![CI](https://github.com/blakee-marcus/kalshi-api-engineering/actions/workflows/verify.yml/badge.svg)](https://github.com/blakee-marcus/kalshi-api-engineering/actions/workflows/verify.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Kalshi docs](https://img.shields.io/badge/source-docs.kalshi.com-blue)](https://docs.kalshi.com/)

---

## It catches things like

```text
✗ Missing /margin in RSA-PSS signing        → every private call 401s
✗ Predictions WS auth reused for Perps      → silent auth failure
✗ Fixed-point prices divided by 100         → 100x mispricing
✗ Stale orderbooks treated as trustworthy   → trades on dead data
✗ Perps code expecting non-existent WS channels (market_lifecycle_v2, market_positions)
```

The skill ships **12 deterministic rules** (`scripts/kalshi_doctor.py`) that scan
your client code and report `PASS` / `WARN` / `FAIL` with the exact file:line,
the official Kalshi source, and a suggested fix.

> **Install this and your agent can automatically find the Kalshi integration bugs LLMs repeatedly generate.**

---

## Why this skill

An AI-generated Kalshi client usually *looks* correct and then fails in one of a
handful of predictable ways. This skill turns those failure modes into a checklist
the agent runs before shipping:

- **Broken auth** — public `200`, private `401`; the fix is signing the full
  `/margin` path. Most integrations hit this first.
- **Broken Perps pricing** — `"0.5600"` parsed as `float` and divided by 100
  becomes `0.0056`. The skill enforces `Decimal("0.5600")`.
- **Broken WS trust** — a sequence gap or reconnect that doesn't invalidate the
  book lets the agent trade on stale data. The skill requires re-snapshot.

Every rule is traced to the **official Kalshi specification** (not a private bot or
personal notes), and a scheduled check re-verifies the specs haven't drifted.

---

## Commands

The skill is a small vocabulary, not one giant instruction surface:

| Command | What it does |
|---------|--------------|
| `/kalshi audit` | Inspect an existing integration for protocol mistakes |
| `/kalshi doctor` | Run the deterministic checker (`scripts/kalshi_doctor.py`) |
| `/kalshi auth` | Diagnose signing / environment / credential-source problems |
| `/kalshi market-data` | Orderbook + WebSocket correctness and trust-state review |
| `/kalshi perps` | Build or debug Perps / Margin integration |
| `/kalshi orders` | Order construction, reconciliation, cancel semantics |
| `/kalshi source` | Resolve a claim against the current Kalshi docs/specs |

> The exact slash-command prefix depends on your runtime (Hermes, Claude Code,
> Codex, Cursor, skills.sh). The skill loads as `SKILL.md` + `references/`; the
> agent routes to the matching playbook.

---

## Quick start (read-only)

```python
import time, base64, requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

KEY_ID, PEM_PATH = "YOUR_KEY_ID", "private_key.pem"
REST = "https://external-api.demo.kalshi.co/trade-api/v2"   # demo: safe read-only

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

# READ-ONLY proof: signed GET to an authenticated margin read endpoint.
r = requests.get(f"{REST}/margin/balance", headers=sign("GET", "/margin/balance", PEM_PATH))
print(r.status_code)  # 200 = signature accepted
```

This skill **never places, amends, or cancels live orders**. Every example is a
read-only `GET`. CI fails if `README.md` or `SKILL.md` embeds a state-changing call.

---

## See it in action

### Broken authentication
```text
Before:  Public 200 / Private 401  → "bad credentials"
Audit:   KALSHI-AUTH-001  signing path missing /margin
After:   signed GET /margin/balance → 200
```

### Broken Perps pricing
```text
Input:   "0.5600"
Buggy:   float("0.5600") / 100  = 0.0056
Skill:   Decimal("0.5600")       = 0.5600
```

### Broken WS trust
```text
snapshot seq=100 → delta 101 → delta 103 (gap)
Bad client:  keeps trading
Skill:       marks book UNTRUSTED, requires fresh snapshot
```

Full runnable versions live in [`examples/`](examples/) (broken + fixed + README).

---

## Coverage

| Surface | Reference | Ingested |
|---------|-----------|----------|
| Predictions — orderbook / canonical-book semantics | `canonical-book-pattern.md` | 2026-08-28 |
| Predictions — forecast percentile | `forecast-percentile-api.md` | 2026-08-28 |
| Predictions — historical candlesticks | `historical-candlesticks-api.md` | 2026-08-28 |
| Predictions — client trades | `client-trades-api.md` | 2026-08-28 |
| Perps / Margin — REST + WS + FIX connectivity, auth, order entry, error codes | `perps-api-connectivity.md` | 2026-08-28 |

Out of scope (read the official specs): full endpoint catalogs beyond the pages
above, account/portfolio reads not summarized in `perps-api-connectivity.md`, FIX
session-replay/certification, Kalshi Academy tutorials. Claims are scoped to the
pages listed; "authoritative reference bank" is **not** claimed for uncovered surfaces.

---

## Supported runtimes

| Runtime | Status |
|---------|--------|
| Hermes | Verified |
| Agent Skills standard (`npx skills add`) | Verified |
| Claude Code / Codex / Cursor | Compatible (loads `SKILL.md` + `references/`) |

Compatibility = the skill loads and routes; it does not imply a harness-specific
integration was separately tested. The checker runs anywhere Python 3.9+ runs.

---

## Installation

```bash
npx skills add blakee-marcus/kalshi-api-engineering
```

Manual (any framework): copy `SKILL.md` and `references/` into your skill dir.
Maintainer-only sync helper: `scripts/maintainer-sync-hermes.sh` (do not run from a
clone you don't maintain).

---

## Source grounding

Every reference page is derived from the **public Kalshi documentation**, not a
private bot or personal notes. See `references/api-documentation-index.md` and
`references/source-manifest.md` (per-page source URL + ingest date).

| Authority | Source |
|-----------|--------|
| Docs home | https://docs.kalshi.com/ |
| Predictions REST | https://docs.kalshi.com/openapi.yaml |
| Perps / Margin REST | https://docs.kalshi.com/perps_openapi.yaml |
| Predictions / Perps WS | asyncapi.yaml / perps_asyncapi.yaml |

A scheduled GitHub Action hashes the official specs and opens an issue when they
change — the skill stays current without manual scraping.

## Safety

- No network calls, no filesystem writes outside install, no credentials.
- No live-trading authorization; any state-changing call needs explicit user
  authorization + an execution boundary outside this skill.
- See [SECURITY.md](SECURITY.md).

## Contributing

Report stale references or new bug patterns via the issue templates
(docs-drift, new-rule, bug). See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
