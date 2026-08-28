#!/usr/bin/env python3
"""Upstream Kalshi spec drift monitor.

Fetches the official Kalshi spec files, hashes them, and opens a GitHub issue
when any hash changes since the last recorded run. State is stored in
`.drift-state.json` (committed so the next run can compare).

Run locally:  python scripts/check_upstream_drift.py
In CI:       scheduled daily; uses GH_TOKEN to open an issue on change.

This is a best-effort monitor. Network/parse failures are reported but do not
crash the run (the scheduled job should not red-fail on a transient fetch error).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / ".drift-state.json"

SPECS = {
    "openapi.yaml": "https://docs.kalshi.com/openapi.yaml",
    "asyncapi.yaml": "https://docs.kalshi.com/asyncapi.yaml",
    "perps_openapi.yaml": "https://docs.kalshi.com/perps_openapi.yaml",
    "perps_asyncapi.yaml": "https://docs.kalshi.com/perps_asyncapi.yaml",
    "llms.txt": "https://docs.kalshi.com/llms.txt",
}

REPO = "blakee-marcus/kalshi-api-engineering"


def _fetch(url: str, timeout: int = 30) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "kalshi-drift-monitor"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print(f"  WARN fetch failed {url}: {e}")
        return None


def main() -> int:
    prev = json.loads(STATE.read_text()) if STATE.exists() else {}
    curr: dict[str, str] = {}
    changed = []

    for name, url in SPECS.items():
        data = _fetch(url)
        if data is None:
            continue
        h = hashlib.sha256(data).hexdigest()[:16]
        curr[name] = h
        if prev.get(name) and prev[name] != h:
            changed.append((name, prev[name], h))

    # persist state
    STATE.write_text(json.dumps(curr, indent=2) + "\n")

    if not changed:
        print("Upstream specs unchanged.")
        return 0

    lines = ["Kalshi upstream spec changed:", ""]
    for name, old, new in changed:
        lines.append(f"- {name}: {old} -> {new}")
    lines.append("")
    lines.append("Action: verify affected reference pages against the new spec "
                 "and open a docs-drift issue if a page is now stale.")
    body = "\n".join(lines)
    print(body)

    # Open a GitHub issue via the API (needs GH_TOKEN)
    token = os.environ.get("GH_TOKEN")
    if token:
        try:
            import urllib.request as u
            api = f"https://api.github.com/repos/{REPO}/issues"
            payload = json.dumps({
                "title": "Upstream Kalshi spec drift detected",
                "body": body,
                "labels": ["docs-drift", "upstream"],
            }).encode()
            req = u.Request(api, data=payload, method="POST", headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "kalshi-drift-monitor",
            })
            with u.urlopen(req, timeout=30) as r:
                print(f"  opened issue: {r.status}")
        except Exception as e:
            print(f"  WARN could not open issue: {e}")
    else:
        print("  (GH_TOKEN not set — skipping issue creation)")

    return 0  # monitor reports; it does not fail the scheduled run


if __name__ == "__main__":
    sys.exit(main())
