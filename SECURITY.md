# Security Policy

`kalshi-api-engineering` is a **documentation / reference skill** for building Kalshi API
clients. It contains no executable trading logic and makes no network calls on its own.

## Credentials

- The skill **contains no credentials** (no API keys, private keys, tokens, or secrets).
- The skill **never asks users to paste private keys** or other secrets.
- Any Kalshi API key / private key used by a client you build is handled entirely in your
  own code and environment, outside this repository.

## Live trading authorization

- The skill **does not authorize live trading**.
- It describes the Kalshi protocol (authentication, order entry, lifecycle, reconciliation)
  but performs no state-changing calls.
- Any `POST` / `DELETE` / `PUT` against Kalshi (place / amend / cancel orders) requires
  **explicit, separate user authorization** in the user's own application. There is no path
  in this skill that triggers such a call.

## Source authority

- Official Kalshi documentation and published specs (`docs.kalshi.com`) are treated as the
  **schema authority**.
- Reference pages cite their official source and ingest date (`references/source-manifest.md`).
- If a reference page disagrees with a published spec, the spec wins.

## Personal-data leakage

- The skill does not read or write any private bot repo, personal notes, chat logs, or
  internal system.
- CI (`.github/workflows/verify.yml`) fails the build on personal absolute paths, internal
  project paths, credential material, bot-specific identifiers, and reference pages without
  a source URL.

## Reporting a problem

If you find a leaked secret, a personal path, or inaccurate safety guidance in this repo,
open an issue or a pull request. Do not include credentials in the report.
