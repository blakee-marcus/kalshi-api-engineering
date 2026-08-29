# Changelog

All notable changes to the public surface of this skill are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- **Drift monitor could never detect change.** `scripts/check_upstream_drift.py`
  stored its baseline in a gitignored `.drift-state.json` that a fresh CI checkout
  discarded every run, so `prev` was always empty and no drift was ever reported.
  The baseline now lives in a committed `[spec-hashes]` block in
  `references/source-manifest.md`, which every checkout carries; the script rewrites
  that block when a hash changes (committed via PR from the drift issue). Added
  `tests/test_check_upstream_drift.py` to guard this regression.

### Changed
- **Softened doctor claims.** The checker is now described as an *experimental
  deterministic lint* with heuristic (whole-file pattern) rules *derived from* the
  official specs, not as automatically finding bugs or being "traced to" the spec.
  README and SKILL.md wording updated accordingly. The rules are unchanged and still
  useful as first-pass review prompts.
## [0.2.0] — 2026-08-28

### Added
- **Deterministic checker** `scripts/kalshi_doctor.py` with 12 rules
  (`KALSHI-AUTH-001` … `KALSHI-EXEC-001`) that scan a Kalshi client for the
  protocol mistakes LLM-generated integrations repeatedly make. Exit code 0 on
  clean code, 1 on any FAIL — usable as a CI gate.
- **pytest suite** `tests/test_kalshi_doctor.py` with positive + negative
  fixtures for every rule (`tests/fixtures/bad/`, `tests/fixtures/good/`).
- **Command vocabulary** routed through `SKILL.md`: `audit`, `doctor`, `auth`,
  `market-data`, `perps`, `orders`, `source` — each with a focused playbook in
  `references/`.
- **Examples** (`examples/`): runnable broken→fixed demos for auth-401,
  perps-fixed-point, and ws-sequence-gap.
- **Contribution infra**: `CONTRIBUTING.md`, `.github/CODEOWNERS`, issue
  templates (bug / docs-drift / new-rule), PR template.
- **Upstream-spec drift monitor** `scripts/check_upstream_drift.py` (scheduled
  daily) that hashes the official Kalshi specs and opens a docs-drift issue on
  change.
- **Extended CI**: detector tests, doctor smoke (bad must fail / good must pass),
  and the daily drift job, in addition to the public-surface gate.

### Changed
- `SKILL.md` reduced from ~13.7 KB monolith to a ~6.4 KB router pointing at
  playbooks; detailed protocol knowledge moved to `references/`.
- README rewritten as a product landing page (outcome-first hero, install above
  the fold, the bugs it catches, "see it in action", provenance, safety).

### Compatibility
- Hermes: verified. Agent Skills standard (`npx skills add`): verified.
  Claude Code / Codex / Cursor: compatible (load `SKILL.md` + `references/`).

### Known gaps
- Per-runtimes (Claude Code / Codex / Cursor) are asserted-compatible, not yet
  separately exercised.
- No generated `dist/` provider packages yet (single source, copied install).
- No `npx kalshi-doctor` distribution yet (run via `python scripts/kalshi_doctor.py`).

## [0.1.0] — 2026-08-28

### Added
- Public-trust reset of the skill: clean source-backed surface, MIT license,
  SECURITY.md, CHANGELOG.md, CI public-surface verification, portable maintainer
  sync helper.
- Read-only demo quickstart (signed `GET` against the demo base); CI fails on
  embedded state-changing requests.
- Seven source-backed reference pages from official Kalshi docs.
