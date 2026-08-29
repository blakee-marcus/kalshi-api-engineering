#!/usr/bin/env python3
"""Upstream Kalshi spec drift monitor.

Fetches the official Kalshi spec files, hashes them, and opens a GitHub issue
when any hash changes since the last recorded run.

IMPORTANT — state persistence:
The previous baseline is stored in a fenced `[spec-hashes]` block inside
`references/source-manifest.md`, which is COMMITTED to the repo. A scheduled
GitHub Action checks out a fresh copy each run, so any state kept in an
untracked/gitignored sidecar file would be lost between runs and drift could
never be detected. Storing the baseline in a tracked file means a fresh checkout
always carries the previous hashes, so a real change is detectable. When a hash
changes, the script rewrites that block in `source-manifest.md` so the next
committed baseline reflects the new spec (the maintainer commits the change, as
the drift issue requests).

Run locally:  python scripts/check_upstream_drift.py
In CI:       scheduled daily; uses GH_TOKEN to open an issue on change.

This is a best-effort monitor. Network/parse failures are reported but do not
crash the run (the scheduled job should not red-fail on a transient fetch error).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "references" / "source-manifest.md"

SPECS = {
    "openapi.yaml": "https://docs.kalshi.com/openapi.yaml",
    "asyncapi.yaml": "https://docs.kalshi.com/asyncapi.yaml",
    "perps_openapi.yaml": "https://docs.kalshi.com/perps_openapi.yaml",
    "perps_asyncapi.yaml": "https://docs.kalshi.com/perps_asyncapi.yaml",
    "llms.txt": "https://docs.kalshi.com/llms.txt",
}

REPO = "blakee-marcus/kalshi-api-engineering"

_HASH_BLOCK_RE = re.compile(r"(?ms)^```\[spec-hashes\]\n(.*?)^```")


def _fetch(url: str, timeout: int = 30) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "kalshi-drift-monitor"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print(f"  WARN fetch failed {url}: {e}")
        return None


def _read_baseline(manifest_text: str) -> dict[str, str]:
    m = _HASH_BLOCK_RE.search(manifest_text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        name, h = line.split("=", 1)
        out[name.strip()] = h.strip()
    return out


def _write_baseline(manifest_text: str, curr: dict[str, str]) -> str:
    block = "```[spec-hashes]\n" + "".join(
        f"{name}={curr[name]}\n" for name in SPECS
    ) + "```"
    if _HASH_BLOCK_RE.search(manifest_text):
        return _HASH_BLOCK_RE.sub(lambda _: block, manifest_text)
    # append if the manifest has no block yet
    return manifest_text.rstrip() + "\n\n## Spec hashes (drift baseline)\n\n" + block + "\n"


def _gh_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "kalshi-drift-monitor",
    }


def find_existing_drift_issue(token: str) -> bool:
    """Return True if an open docs-drift issue already exists.

    Dedupe guard: a spec change detected before the maintainer merges the
    baseline-update PR would otherwise spawn a new issue on every scheduled run.
    On a transient API failure we conservatively assume one exists (skip), so a
    flaky network call can never cause duplicate-issue spam; the next healthy run
    re-checks.
    """
    try:
        api = f"https://api.github.com/repos/{REPO}/issues"
        req = urllib.request.Request(
            f"{api}?labels=docs-drift,upstream&state=open",
            headers=_gh_headers(token))
        with urllib.request.urlopen(req, timeout=30) as r:
            issues = json.loads(r.read())
        return any("drift" in (iss.get("title", "")).lower() for iss in issues)
    except Exception as e:
        print(f"  WARN could not check for existing drift issue: {e}")
        return True


def open_drift_issue(body: str, token: str) -> None:
    """Open a docs-drift GitHub issue describing the changed specs."""
    api = f"https://api.github.com/repos/{REPO}/issues"
    payload = json.dumps({
        "title": "Upstream Kalshi spec drift detected",
        "body": body,
        "labels": ["docs-drift", "upstream"],
    }).encode()
    req = urllib.request.Request(api, data=payload, method="POST",
                                 headers=_gh_headers(token))
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"  opened issue: {r.status}")


def main() -> int:
    if not MANIFEST.exists():
        print(f"ERROR: {MANIFEST} missing — cannot read drift baseline.")
        return 1

    manifest_text = MANIFEST.read_text()
    prev = _read_baseline(manifest_text)
    curr: dict[str, str] = {}
    changed = []

    for name, url in SPECS.items():
        data = _fetch(url)
        if data is None:
            # keep the previous known hash if we have one, so a transient fetch
            # failure does not masquerade as "changed to unknown".
            if name in prev:
                curr[name] = prev[name]
            continue
        h = hashlib.sha256(data).hexdigest()[:16]
        curr[name] = h
        if prev.get(name) and prev[name] != h:
            changed.append((name, prev[name], h))

    # persist the new baseline back into the committed manifest
    MANIFEST.write_text(_write_baseline(manifest_text, curr))

    if not changed:
        print("Upstream specs unchanged.")
        return 0

    lines = ["Kalshi upstream spec changed:", ""]
    for name, old, new in changed:
        lines.append(f"- {name}: {old} -> {new}")
    lines.append("")
    lines.append("Action: verify affected reference pages against the new spec "
                 "and open a docs-drift issue if a page is now stale. The baseline "
                 "in references/source-manifest.md has been updated to the new hash; "
                 "commit it via a PR.")
    body = "\n".join(lines)
    print(body)

    # Open a GitHub issue via the API (needs GH_TOKEN). Guard against duplicate
    # issues: if an open drift issue already exists (maintainer hasn't merged the
    # baseline update yet), skip rather than spam a new one each run.
    token = os.environ.get("GH_TOKEN")
    if not token:
        print("  (GH_TOKEN not set — skipping issue creation)")
    elif find_existing_drift_issue(token):
        print("  open drift issue already exists — skipping duplicate "
              "(update the baseline via the existing issue's PR).")
    else:
        open_drift_issue(body, token)

    return 0  # monitor reports; it does not fail the scheduled run


if __name__ == "__main__":
    sys.exit(main())
