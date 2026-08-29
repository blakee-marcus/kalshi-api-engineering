# Guide for agents

This file explains how to change `kalshi-api-engineering` without breaking the skill, its safety boundaries, or its distribution surfaces.

## What this repo contains

`kalshi-api-engineering` is a portable agent skill for building and reviewing Kalshi API integrations.

It contains documentation, examples, source-backed references, an experimental deterministic heuristic checker, and an upstream-spec drift monitor.

It is **not a trading bot**.

Keep the repository portable. Do not add instructions that depend on one agent runtime, one local machine, private workspace state, or personal filesystem paths.

## Key files

- `SKILL.md` — the agent-facing router and product entry point. Keep it concise; detailed protocol guidance belongs in `references/`.
- `references/` — source-backed Kalshi API playbooks and technical references.
- `references/source-manifest.md` — provenance plus the committed upstream-spec hash baseline.
- `scripts/kalshi_doctor.py` — deterministic whole-file heuristic checks for common integration mistakes.
- `scripts/check_upstream_drift.py` — monitors official Kalshi specs for changes.
- `scripts/verify_public_surface.py` — checks the repository for packaging, provenance, and public-surface problems.
- `tests/` — doctor fixtures and drift-monitor regression tests.
- `examples/` — small examples that demonstrate supported patterns and failure modes.
- `.claude-plugin/plugin.json` — Claude plugin metadata.
- `.github/workflows/verify.yml` — CI and scheduled drift verification.

## Rules for changes

### Preserve the safety boundary

The skill may document Kalshi's state-changing API surfaces, but repository examples and verification code must not place, amend, cancel, or otherwise execute live trades.

Do not add credentials, private keys, tokens, signing material, or real account data.

Do not add private project names, personal paths, local runtime state, internal audit artifacts, or other non-public implementation details.

### Use current Kalshi sources

For API behavior, use this authority order:

1. Current official Kalshi endpoint or WebSocket documentation.
2. Current OpenAPI or AsyncAPI specifications.
3. Current Kalshi changelog.
4. Observed API behavior when it exposes a documented discrepancy.
5. This repository's references.

Do not treat an old implementation, search snippet, or bundled reference as stronger evidence than the current official API surface.

### Keep the router lean

Treat the prompt in `SKILL.md` as the product.

Prefer a short routing rule or invariant over copying protocol detail into the root skill. Put durable technical depth in the appropriate reference file.

When adding a new workflow, first decide whether it belongs in an existing playbook before creating another top-level concept.

### Keep references traceable

Every implementation-sensitive reference must identify its official source.

When upstream behavior changes:

- inspect the actual source change;
- update affected guidance, examples, checker rules, or tests;
- then update the committed spec-hash baseline.

Do not accept a new hash merely to silence the drift monitor.

Do not move drift state into an untracked or gitignored sidecar file. Fresh CI checkouts must carry the previous baseline.

### Treat the doctor as a heuristic checker

Doctor rules are deterministic, but they are not semantic program analysis.

Do not describe a regex finding as proof that code is correct or incorrect.

When changing a doctor rule:

- keep the rule narrowly scoped;
- add or update a failing fixture under `tests/fixtures/bad/`;
- add or update a passing fixture under `tests/fixtures/good/`;
- avoid broad patterns that create obvious false positives;
- update user-facing documentation when the rule's meaning changes.

### Keep package metadata synchronized

When the release version changes, keep the version in `SKILL.md` and `.claude-plugin/plugin.json` aligned.

Update `CHANGELOG.md` and any README release/version material for behavior changes or non-obvious fixes.

Keep installation and usage instructions portable across compatible agents. Individual agent products may be examples, but should not become unnecessary requirements.

## Writing style

Use plain technical language.

- Lead with the rule or conclusion.
- Use active voice.
- Keep sentences and paragraphs short.
- Use one term consistently for the same concept.
- Use `must` for requirements.
- Remove repeated warnings and historical explanation.
- Preserve exact endpoint names, field names, commands, paths, identifiers, and API terminology.
- Distinguish verified API behavior from inference.
- Do not overstate what a heuristic, test, or component-level probe proves.

## Before you commit

Run:

```bash
python3 -m pytest tests/ -q
python3 scripts/verify_public_surface.py
npx --yes skills@latest add . --list
claude plugin validate . --strict
```

For doctor changes, also verify both fixture classes directly:

```bash
python3 scripts/kalshi_doctor.py tests/fixtures/bad
python3 scripts/kalshi_doctor.py tests/fixtures/good
```

Expected behavior:

- bad fixtures exit `1`;
- good fixtures exit `0`;
- pytest passes;
- public-surface verification reports `Public surface clean`;
- skill discovery finds `kalshi-api-engineering`;
- Claude plugin validation passes.

## Releasing

Do not publish from an unverified tree.

Before tagging a release:

1. Push the intended release commit.
2. Confirm the GitHub Actions workflow is green for that exact commit.
3. Confirm skill discovery and plugin validation actually ran successfully.
4. Confirm `SKILL.md`, plugin metadata, changelog, and release version agree.
5. Create the tag and GitHub Release only with explicit publication approval.

A local pass is necessary but does not replace the clean pushed-tree CI gate.
