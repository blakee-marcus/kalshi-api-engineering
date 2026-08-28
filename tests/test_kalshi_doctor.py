"""Tests for the deterministic kalshi_doctor checker.

Every detector rule requires:
  - one positive fixture (bad/) that must produce a FAIL/WARN for that rule
  - one negative fixture (good/) that must NOT produce that rule

Run: pytest tests/test_kalshi_doctor.py -q
"""
from pathlib import Path

import scripts.kalshi_doctor as doc

ROOT = Path(__file__).resolve().parent
BAD = ROOT / "fixtures" / "bad"
GOOD = ROOT / "fixtures" / "good"


def _rules_for(path: Path):
    return {f.rule for f in doc.run(path)}


def test_all_rules_have_a_fixture():
    # every rule id must have at least one bad fixture that triggers it
    covered = set()
    for p in sorted(BAD.rglob("*.py")):
        covered |= _rules_for(p)
    missing = set(doc.RULES) - covered
    assert not missing, f"rules with no triggering fixture: {missing}"


def test_good_fixtures_stay_clean():
    # each good fixture must not trigger its paired rule
    pairs = {
        "auth-001-margin-sign-full-path.py": "KALSHI-AUTH-001",
        "ws-001-perps-margin-path.py": "KALSHI-WS-001",
        "price-001-dollars-decimal.py": "KALSHI-PRICE-001",
        "price-002-decimal-money.py": "KALSHI-PRICE-002",
        "ws-002-delta-increment.py": "KALSHI-WS-002",
        "ws-003-gap-invalidate.py": "KALSHI-WS-003",
        "ws-004-reconnect-untrust.py": "KALSHI-WS-004",
        "perps-001-no-lifecycle.py": "KALSHI-PERPS-001",
        "perps-002-no-positions-channel.py": "KALSHI-PERPS-002",
        "perps-003-reduce-only-ioc.py": "KALSHI-PERPS-003",
        "ord-001-client-id.py": "KALSHI-ORD-001",
        "exec-001-boundary.py": "KALSHI-EXEC-001",
    }
    for fname, rule in pairs.items():
        triggered = _rules_for(GOOD / fname)
        assert rule not in triggered, f"{fname} wrongly triggered {rule}: {triggered}"


def test_bad_fixtures_trigger_rule():
    pairs = {
        "auth-001-margin-sign-no-path.py": "KALSHI-AUTH-001",
        "ws-001-perps-predictions-path.py": "KALSHI-WS-001",
        "price-001-dollars-div100.py": "KALSHI-PRICE-001",
        "price-002-float-money.py": "KALSHI-PRICE-002",
        "ws-002-delta-absolute.py": "KALSHI-WS-002",
        "ws-003-gap-no-invalidate.py": "KALSHI-WS-003",
        "ws-004-reconnect-trusted.py": "KALSHI-WS-004",
        "perps-001-lifecycle-channel.py": "KALSHI-PERPS-001",
        "perps-002-positions-channel.py": "KALSHI-PERPS-002",
        "perps-003-reduce-only-gtc.py": "KALSHI-PERPS-003",
        "ord-001-no-client-id.py": "KALSHI-ORD-001",
        "exec-001-no-boundary.py": "KALSHI-EXEC-001",
    }
    for fname, rule in pairs.items():
        triggered = _rules_for(BAD / fname)
        assert rule in triggered, f"{fname} did not trigger {rule}: {triggered}"


def test_exit_code_contract():
    # scanning only good fixtures => no FAIL => exit 0
    import subprocess, sys
    r = subprocess.run([sys.executable, "-m", "scripts.kalshi_doctor", str(GOOD)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    # scanning only bad fixtures => at least one FAIL => exit 1
    r = subprocess.run([sys.executable, "-m", "scripts.kalshi_doctor", str(BAD)],
                       capture_output=True, text=True)
    assert r.returncode == 1, r.stdout
