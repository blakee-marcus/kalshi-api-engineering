# Maintenance contract — kalshi-api-engineering

This is the source repo for the `kalshi-api-engineering` agent skill. It is
documentation + a deterministic checker, **not a trading bot**. Read this before
changing the repo.

> Note: this file is named `MAINTAINERS.md` because the runtime blocks writing a
> file literally named `AGENTS.md` in this repo. If you want the portable
> cross-agent `AGENTS.md` convention (auto-loaded by Hermes/Claude/Codex), rename
> it with `git mv MAINTAINERS.md AGENTS.md` after the guard is relaxed. The
> content is the same.

## Non-negotiable boundaries
- **No live orders.** The skill never places, amends, or cancels trades. Any
  state-changing Kalshi call requires explicit, separate user authorization
  outside this skill.
- **No credentials, no private keys.** Never add API keys, private keys, or
  signing material. Examples are read-only `GET` only; CI fails on embedded
  state-changing calls.
- **No private-repo leakage.** Do not reference `kashiBot`, `~/.hermes/projects`,
  personal paths, Obsidian, Telegram, or internal audit artifacts. CI's
  `verify_public_surface.py` fails on leaks.

## What lives here
- `SKILL.md` — router. Keep it lean (~6 KB); put protocol detail in `references/`.
- `references/` — command playbooks + source-backed pages. Every page must cite
  an official source URL at the top (CI enforces this).
- `scripts/kalshi_doctor.py` — the heuristic checker (whole-file regex rules).
- `scripts/check_upstream_drift.py` — scheduled spec-drift monitor.
- `tests/` — positive + negative fixtures for every doctor rule; drift tests.

## Authority order
1. Current official Kalshi docs / published specs (docs.kalshi.com).
2. Observed API behavior when it diverges from the docs.
3. This skill's reference pages.
4. Prior implementations, only when explicitly consulted.

## Upstream drift baseline
`scripts/check_upstream_drift.py` compares fetched spec hashes against the
committed `[spec-hashes]` block in `references/source-manifest.md` (a fresh CI
checkout carries it, so drift is actually detectable). When a hash changes the
job opens a `docs-drift` issue and rewrites the block; merge the resulting PR to
update the baseline. Do **not** put drift state in an untracked/gitignored file.

## Before you commit
- `python3 -m pytest tests/ -q` — must pass.
- `python3 scripts/verify_public_surface.py` — must report "Public surface clean".
- Doctor rules need a positive (`tests/fixtures/bad/`) and negative
  (`tests/fixtures/good/`) fixture each.

## Releasing
- Tag `vX.Y.Z` only after the CI workflow is green on a clean pushed tree.
- Create the GitHub Release separately, only after packaging checks (skill
  discovery + `claude plugin validate`) are green. Do not push or publish
  without explicit approval.
