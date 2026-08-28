#!/usr/bin/env python3
"""kalshi_doctor — deterministic checks for Kalshi integration bugs.

Scans a directory of Kalshi client code (Python + any text) for the protocol
mistakes LLM-generated integrations repeatedly make. Each check is a *rule* with
a stable id, so output is greppable and CI-friendly.

Usage:
    python scripts/kalshi_doctor.py .
    python scripts/kalshi_doctor.py ./my_client --json
    python scripts/kalshi_doctor.py path/to/file.py

Exit code: 0 if no FAIL, 1 if any FAIL (so CI can gate on it).

This tool is READ-ONLY. It never modifies, sends, or executes anything. It is
documentation-adjacent: every finding points at the official source it is
derived from (docs.kalshi.com specs), not at a private bot.

Rules (see references/ for the playbook behind each):
    KALSHI-AUTH-001  margin signing omits /margin
    KALSHI-WS-001    predictions WS auth path reused for perps
    KALSHI-PRICE-001 _dollars parsed as float / divided by 100
    KALSHI-PRICE-002 binary float used for Kalshi money/price
    KALSHI-WS-002    orderbook delta treated as absolute, not incremental
    KALSHI-WS-003    WS sequence gap does not invalidate trust
    KALSHI-WS-004    reconnect reuses old snapshot as trusted
    KALSHI-PERPS-001 perps code expects market_lifecycle_v2
    KALSHI-PERPS-002 perps code expects market_positions
    KALSHI-PERPS-003 reduce_only=true combined with GTC
    KALSHI-ORD-001   order creation lacks stable client_order_id
    KALSHI-EXEC-001  state-changing prod call without explicit boundary
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# ---- rule registry -------------------------------------------------------

SOURCE = "https://docs.kalshi.com/ (openapi.yaml, perps_openapi.yaml, asyncapi.yaml, perps_asyncapi.yaml)"

RULES = {
    "KALSHI-AUTH-001": "Margin REST request signed without the /margin path segment.",
    "KALSHI-WS-001": "Predictions WebSocket auth path reused for Perps / Margin WebSocket.",
    "KALSHI-PRICE-001": "Fixed-point *_dollars divided by 100 (or parsed via float).",
    "KALSHI-PRICE-002": "Binary float used for Kalshi money/price instead of Decimal.",
    "KALSHI-WS-002": "Orderbook delta treated as absolute assignment, not increment.",
    "KALSHI-WS-003": "WebSocket sequence gap does not invalidate book trust.",
    "KALSHI-WS-004": "Reconnect reuses an old snapshot as trusted.",
    "KALSHI-PERPS-001": "Perps code expects market_lifecycle_v2 channel (does not exist on margin WS).",
    "KALSHI-PERPS-002": "Perps code expects market_positions channel (does not exist on margin WS).",
    "KALSHI-PERPS-003": "reduce_only=true combined with good_till_canceled (margin API rejects).",
    "KALSHI-ORD-001": "Order creation does not carry a stable client_order_id.",
    "KALSHI-EXEC-001": "State-changing production call with no explicit execution boundary.",
}


@dataclass
class Finding:
    rule: str
    severity: str  # FAIL | WARN
    path: str
    line: int
    snippet: str
    why: str
    fix: str


SUGGESTED = {
    "KALSHI-AUTH-001": "Sign the full /trade-api/v2/margin/... path for every margin REST request.",
    "KALSHI-WS-001": "Use /trade-api/ws/v2/margin for Perps WS auth, never the predictions path.",
    "KALSHI-PRICE-001": "Parse Decimal(price_dollars) verbatim; do NOT divide by 100.",
    "KALSHI-PRICE-002": "Parse money/price as Decimal from string; never binary float.",
    "KALSHI-WS-002": "Apply deltas as increments: levels[p] = levels.get(p, 0) + delta (pop on 0).",
    "KALSHI-WS-003": "On any sequence gap, mark the book UNTRUSTED and demand a fresh snapshot.",
    "KALSHI-WS-004": "After reconnect, reset to UNTRUSTED until a fresh snapshot arrives.",
    "KALSHI-PERPS-001": "Drop market_lifecycle_v2; use margin REST for position/account state.",
    "KALSHI-PERPS-002": "Drop market_positions; use margin REST /positions + private streams.",
    "KALSHI-PERPS-003": "reduce_only is valid only with immediate_or_cancel or fill_or_kill.",
    "KALSHI-ORD-001": "Generate and preserve a stable client_order_id on every create.",
    "KALSHI-EXEC-001": "Gate state-changing calls behind an explicit, user-authorized write flag.",
}


# ---- detectors -----------------------------------------------------------

CODE_EXT = {".py", ".js", ".ts", ".tsx", ".go", ".rs", ".java", ".rb"}


def _iter_targets(root: Path):
    if root.is_file():
        yield root
        return
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if ".git" in p.parts:
            continue
        if p.suffix not in CODE_EXT:
            continue  # only scan code, never our own .md docs
        # when self-scanning this meta-repo, skip our own skill internals
        if "kashi" in p.parts and ("references" in p.parts or "scripts" in p.parts):
            continue
        yield p


def _line_of(text: str, needle: str, default: int = 1) -> int:
    for i, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return i
    return default


def _scan(path: Path):
    try:
        text = path.read_text(errors="replace")
    except Exception:
        return
    low = text.lower()
    rel = str(path)
    F = []

    def add(rule, sev, needle, why):
        F.append(Finding(rule, sev, rel, _line_of(text, needle), needle.strip()[:120], why, SUGGESTED[rule]))

    # KALSHI-AUTH-001: margin REST signing without the /margin path segment
    # Only fires on REST margin endpoints (portfolio/balance, margin/orders, ...),
    # not on WS auth paths that legitimately use /trade-api/ws/v2/margin.
    if re.search(r"sign\s*\(", low) and re.search(r"/trade-api/v2/margin", low) is None \
            and ("portfolio/balance" in low or "margin/orders" in low
                 or "/margin/positions" in low or "/margin/balance" in low):
        add("KALSHI-AUTH-001", "FAIL", "sign(",
            "Margin request signing must cover the full /trade-api/v2/margin/... path.")

    # KALSHI-WS-001: perps/margon WS reusing predictions auth path
    if (("perps" in low or "margin" in low) and re.search(r"trade-api/ws/v2", low)
            and not re.search(r"trade-api/ws/v2/margin", low)):
        add("KALSHI-WS-001", "FAIL", "trade-api/ws/v2",
            "Perps WS must auth on /trade-api/ws/v2/margin, not the predictions path.")

    # KALSHI-PRICE-001: fixed-point divided by 100
    if re.search(r"/\s*100\b", text) and ("dollar" in low or "price" in low or "_fp" in low):
        m = re.search(r".{0,40}/\s*100\b.{0,20}", text)
        add("KALSHI-PRICE-001", "FAIL", m.group(0) if m else "/100",
            "Fixed-point prices are already 4-decimal strings; dividing by 100 underprices 100x.")

    # KALSHI-PRICE-002: binary float for money/price
    if re.search(r"float\s*\(\s*[a-z_]*price", low) or re.search(r"float\s*\(\s*[a-z_]*dollar", low):
        m = re.search(r"float\s*\([a-z_]*", low)
        add("KALSHI-PRICE-002", "WARN", m.group(0) if m else "float(",
            "Parsing money/price via float() loses decimal precision; use Decimal.")

    # KALSHI-WS-002: delta as absolute assignment, not increment
    if re.search(r"delta", low) and re.search(r"=\s*delta\b", text) \
            and not (re.search(r"levels\.get", text) or "+=" in text or "increment" in low):
        add("KALSHI-WS-002", "FAIL", "= delta",
            "Deltas are increments to level size, not absolute assignment.")

    # KALSHI-WS-003: sequence gap without trust invalidation
    if re.search(r"seq|sequence", low, re.I) and "gap" in low \
            and not re.search(r"\b(untrust|invalid|resync|resnapshot|fresh)\b", low):
        add("KALSHI-WS-003", "WARN", "gap",
            "A sequence gap must invalidate book trust and force a fresh snapshot.")

    # KALSHI-WS-004: reconnect reuses old snapshot as trusted
    if ("reconnect" in low or "resubscribe" in low) \
            and re.search(r"trusted\s*=\s*True|trust\s*=\s*True|trusted=True", text) \
            and not re.search(r"\b(fresh|untrust)\b", low):
        add("KALSHI-WS-004", "WARN", "reconnect",
            "After reconnect, reset to UNTRUSTED until a fresh snapshot is verified.")

    # KALSHI-PERPS-001: non-existent market_lifecycle_v2 channel
    if "market_lifecycle_v2" in low:
        add("KALSHI-PERPS-001", "FAIL", "market_lifecycle_v2",
            "market_lifecycle_v2 does not exist on margin WS.")

    # KALSHI-PERPS-002: non-existent market_positions channel
    if "market_positions" in low:
        add("KALSHI-PERPS-002", "FAIL", "market_positions",
            "market_positions channel does not exist on margin WS.")

    # KALSHI-PERPS-003: reduce_only + good_till_canceled
    if "reduce_only" in low and "good_till_canceled" in low:
        add("KALSHI-PERPS-003", "FAIL", "reduce_only",
            "reduce_only is rejected with GTC; use immediate_or_cancel or fill_or_kill.")

    # KALSHI-ORD-001: create without client_order_id
    if re.search(r"create_order|\.create\(|new_order|place_order|order_create", low) \
            and "client_order_id" not in low:
        add("KALSHI-ORD-001", "WARN", "create",
            "Every order create should carry a stable client_order_id for reconciliation.")

    # KALSHI-EXEC-001: state-changing call without an explicit boundary
    if re.search(r"requests\.(post|put|patch|delete)\s*\(", low) or re.search(r"\.(post|put|patch|delete)\s*\(", low):
        if not re.search(r"write_enabled|dry_run|authoriz", low):
            add("KALSHI-EXEC-001", "FAIL", "requests.delete",
                "State-changing calls need an explicit, user-authorized execution boundary.")

    return F


def run(root: Path) -> list[Finding]:
    found: list[Finding] = []
    for p in _iter_targets(root):
        if "kashi" in p.parts and ("references" in p.parts or "scripts" in p.parts):
            continue  # don't flag our own skill internals
        found.extend(_scan(p))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic Kalshi integration checker.")
    ap.add_argument("path", nargs="?", default=".", help="file or directory to scan")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    findings = run(root)

    if args.json:
        out = [{"rule": f.rule, "severity": f.severity, "path": f.path, "line": f.line,
                "snippet": f.snippet, "why": f.why, "fix": f.fix, "source": SOURCE} for f in findings]
        print(json.dumps(out, indent=2))
        return 1 if any(f.severity == "FAIL" for f in findings) else 0

    print(f"\nkalshi_doctor — scanning {root}\n{'=' * 60}")
    if not findings:
        print("  No protocol mistakes detected. (PASS)")
        return 0
    fails = [f for f in findings if f.severity == "FAIL"]
    warns = [f for f in findings if f.severity == "WARN"]
    for f in findings:
        mark = "FAIL" if f.severity == "FAIL" else "WARN"
        print(f"\n  [{mark}] {f.rule}  {f.path}:{f.line}")
        print(f"         {f.why}")
        print(f"         found: {f.snippet}")
        print(f"         fix:   {f.fix}")
        print(f"         src:   {SOURCE}")
    print(f"\n{'=' * 60}")
    print(f"  {len(fails)} FAIL, {len(warns)} WARN across {len(findings)} finding(s).")
    print("  Rules: " + ", ".join(sorted(RULES)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
