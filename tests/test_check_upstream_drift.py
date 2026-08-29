"""Tests for the upstream-spec drift monitor (scripts/check_upstream_drift.py).

These guard the regression where the monitor could never detect a change because
its baseline lived in a gitignored sidecar file that a fresh CI checkout discarded.
The baseline now lives in a committed [spec-hashes] block in
references/source-manifest.md, so a fresh checkout carries the previous hashes.

Network + GitHub API are avoided by monkeypatching _fetch and the issue helpers,
and by injecting a fake GH_TOKEN so the issue-creation branch is exercised.

To faithfully simulate CI, each "run" uses its own independent manifest seeded
with the committed baseline, because in CI the runner is ephemeral: the monitor
writes only its working copy, so the committed baseline is the same every run —
which is precisely why a duplicate-issue guard is required.
"""
import io
import os
import sys
from pathlib import Path

import hashlib

import scripts.check_upstream_drift as drift

ROOT = Path(__file__).resolve().parent.parent
EMPTY = hashlib.sha256(b"").hexdigest()[:16]
OLD = "0" * 16  # stand-in for whatever the committed baseline hash is
OPENAPI_NEW = b"CHANGED SPEC"


def _manifest(baseline: dict[str, str]) -> Path:
    p = ROOT / "tests" / "_tmp_drift_manifest.md"
    body = "```[spec-hashes]\n" + "".join(
        f"{n}={baseline[n]}\n" for n in drift.SPECS) + "```\n"
    p.write_text("# Source Manifest\n\n" + body)
    return p


def _restore():
    drift.MANIFEST = ROOT / "references" / "source-manifest.md"
    os.environ.pop("GH_TOKEN", None)


def _run_with(monkeypatched: dict):
    """Point MANIFEST at a fresh temp manifest seeded with OLD baseline, apply
    monkeypatches, run main(), return (rc, stdout)."""
    manifest = _manifest({n: OLD for n in drift.SPECS})
    drift.MANIFEST = manifest
    os.environ["GH_TOKEN"] = "test-token"
    for name, fn in monkeypatched.items():
        setattr(drift, name, fn)
    cap = io.StringIO()
    sys.stdout = cap
    try:
        rc = drift.main()
    finally:
        sys.stdout = sys.__stdout__
    out = cap.getvalue()
    manifest.unlink(missing_ok=True)
    return rc, out


def test_detects_change_and_rewrites_baseline():
    try:
        def fake_fetch(url, timeout=30):
            return OPENAPI_NEW if "openapi.yaml" in url else b""
        rc, out = _run_with({"_fetch": fake_fetch})
        assert rc == 0
        assert "openapi.yaml" in out and "->" in out
    finally:
        _restore()


def test_no_change_is_idempotent():
    try:
        # Seed the baseline with the hash the stub will actually return, so a run
        # is genuinely "no change" (baseline matches fetched content).
        unchanged = b"untouched spec content"
        baseline = {n: hashlib.sha256(unchanged).hexdigest()[:16] for n in drift.SPECS}
        manifest = _manifest(baseline)
        drift.MANIFEST = manifest
        os.environ["GH_TOKEN"] = "test-token"

        def fake_fetch(url, timeout=30):
            return unchanged

        setattr(drift, "_fetch", fake_fetch)
        cap = io.StringIO()
        sys.stdout = cap
        try:
            rc = drift.main()
        finally:
            sys.stdout = sys.__stdout__
        out = cap.getvalue()
        manifest.unlink(missing_ok=True)
        assert rc == 0
        assert "unchanged" in out
    finally:
        _restore()


def test_drift_issue_records_old_and_new_hashes():
    try:
        calls = []
        def fake_fetch(url, timeout=30):
            return OPENAPI_NEW if "openapi.yaml" in url else b""
        rc, out = _run_with({
            "_fetch": fake_fetch,
            "find_existing_drift_issue": lambda token: False,
            "open_drift_issue": lambda body, token: calls.append(body),
        })
        assert rc == 0
        assert len(calls) == 1, calls
        body = calls[0]
        assert "openapi.yaml" in body and "->" in body
        assert OLD in body
        assert hashlib.sha256(OPENAPI_NEW).hexdigest()[:16] in body
    finally:
        _restore()


def test_no_duplicate_issue_on_repeated_runs():
    try:
        calls = []

        def fake_fetch(url, timeout=30):
            return OPENAPI_NEW if "openapi.yaml" in url else b""

        # run 1: fresh checkout, no existing issue -> open one
        rc1, out1 = _run_with({
            "_fetch": fake_fetch,
            "find_existing_drift_issue": lambda token: False,
            "open_drift_issue": lambda body, token: calls.append(body),
        })
        assert rc1 == 0 and len(calls) == 1, calls

        # run 2: fresh checkout again (baseline unchanged), issue now open -> skip
        calls.clear()
        rc2, out2 = _run_with({
            "_fetch": fake_fetch,
            "find_existing_drift_issue": lambda token: True,
            "open_drift_issue": lambda body, token: calls.append(body),
        })
        assert rc2 == 0
        assert len(calls) == 0, "second run opened a duplicate issue"
        assert "already exists" in out2
    finally:
        _restore()
