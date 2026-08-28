# source

> Official source: https://docs.kalshi.com/llms.txt
> Last ingested: 2026-08-28
> Scope: authority order and continuous drift-check procedure.

Resolve an assertion against the exact current Kalshi documentation / specs.

## When to use
- "Is this still true in the current Kalshi API?"
- A reference page may be stale vs the published spec.

## Authority order (non-negotiable)
1. Current official Kalshi docs / published specs (docs.kalshi.com).
2. Observed API behavior when it diverges from the docs.
3. This skill's reference pages.
4. Prior implementations, only when explicitly consulted.

Treat the official OpenAPI / AsyncAPI specs as schema authority. If a reference
page disagrees with a published spec, the spec wins and the page should be
corrected (open a docs-drift issue — see `CONTRIBUTING.md`).

## Official sources
| Surface | URL |
|---------|-----|
| Docs home | https://docs.kalshi.com/ |
| Page index | https://docs.kalshi.com/llms.txt |
| Predictions REST | https://docs.kalshi.com/openapi.yaml |
| Predictions WS | https://docs.kalshi.com/asyncapi.yaml |
| Perps / Margin REST | https://docs.kalshi.com/perps_openapi.yaml |
| Perps / Margin WS | https://docs.kalshi.com/perps_asyncapi.yaml |

## Continuous drift check
A scheduled GitHub Action fetches the four spec files + `llms.txt`, hashes them,
and opens an issue when a hash changes. This is how the skill stays current
without manual scraping.

## Completion
- The assertion is traced to a specific official URL + fetched date, or marked
  as unverified pending a spec fetch.
