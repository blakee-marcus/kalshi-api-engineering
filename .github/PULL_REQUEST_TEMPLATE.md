<!-- PR template -->
## What
<!-- one line: what changes -->

## Rule / page affected
<!-- KALSHI-XXX-NNN, or reference page, or CI -->

## Official source
<!-- URL to docs.kalshi.com spec/page this is derived from -->

## Checklist
- [ ] `python scripts/verify_public_surface.py` passes
- [ ] `python -m pytest tests/test_kalshi_doctor.py -q` passes
- [ ] Every new rule has a `tests/fixtures/bad/` + `tests/fixtures/good/` pair
- [ ] No credentials / internal paths / state-changing examples added
- [ ] `references/source-manifest.md` updated with source + ingest date
