# Contributing

Thanks for helping make Kalshi integrations correct.

## What this repo is

A source-backed agent skill: `SKILL.md` + `references/` (playbooks) + a
deterministic checker (`scripts/kalshi_doctor.py`). It is documentation and a
linter, **not a trading bot** and **not a strategy**.

## Ways to contribute

- **Docs drift** — Kalshi changed an endpoint/spec and a reference page is stale.
- **New rule** — you found a protocol mistake LLM-generated clients make; add a
  detector.
- **Bug** — the checker misfires (false positive/negative) or a playbook is wrong.

## Adding a detector rule (the main contribution path)

1. Reproduce the bug in `tests/fixtures/bad/<rule>.py`.
2. Add the matching correct version in `tests/fixtures/good/<rule>.py`.
3. Implement the detector in `scripts/kalshi_doctor.py` with a stable
   `KALSHI-<SURFACE>-<NNN>` id.
4. Add positive + negative assertions in `tests/test_kalshi_doctor.py`.
5. Document the rule in `references/doctor.md` and the relevant playbook.

Every rule must trace to an **official Kalshi source** (docs.kalshi.com spec),
not a private bot or personal note. Record the source + ingest date in
`references/source-manifest.md`.

## Provenance rules

- Do not add credentials, API keys, private keys, or internal bot paths.
- Keep every README/SKILL example **read-only** (`GET`); never embed a
  state-changing call. CI fails on violations.
- Reference pages must carry an official source URL + ingest date.

## Running checks locally

```bash
python scripts/verify_public_surface.py   # public-surface gate
python -m pytest tests/test_kalshi_doctor.py -q   # detector rules
python scripts/kalshi_doctor.py <path>    # manual scan
```

## Issue templates

Use the provided templates: `bug.yml`, `docs-drift.yml`, `new-rule.yml`.
