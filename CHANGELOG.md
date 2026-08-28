# Changelog

All notable changes to the public surface of this skill are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project
adheres to [Semantic Versioning](https://semver.org/) once a `v0.1.0` tag is cut.

## [Unreleased] — public-trust reset

This is the first public-facing cleanup. It is **not** yet tagged `v0.1.0` until CI passes
and the history is verified clean.

### Added
- `README.md` rewritten for external users: purpose, provenance, read-only vs
  state-changing boundaries, permissions/tools, what-it-will-not-do, coverage table,
  standard install, supported runtimes, verification methodology.
- `SECURITY.md`: no credentials, no private-key prompts, no live-trading authorization,
  explicit state-change authorization, official-docs authority.
- `CHANGELOG.md`.
- `.github/workflows/verify.yml` + `scripts/verify_public_surface.py`: CI guards the public
  surface (frontmatter, required files, no personal paths, no credentials, no broken links,
  no bot-specific identifiers, source-URL on every reference).
- `references/api-documentation-index.md` and `references/source-manifest.md` for provenance.

### Changed
- `SKILL.md` rewritten as a portable API-engineering reference: removed all project/bot-
  specific content (bot paths, activation commands, personal-note references, strategy/
  calibration phases, internal source paths, claimed bot architecture). Added explicit
  "what it will NOT do" and authority-order sections.
- `references/perps-api-connectivity.md` scrubbed of bot-specific mentions.
- `scripts/install.sh` renamed to `scripts/maintainer-sync-hermes.sh` (maintainer-only;
  portable hashing for macOS) and de-emphasized in docs.

### Removed
- 16 project-history reference files (dated bot audits, implementation notes,
  consolidation plans, live-inspection dumps, phase-specific artifacts, empty compliance
  file) evicted from the public surface; they belong in the bot repo / private history.

### Not changed
- `LICENSE` (MIT, Blake Marcus).
