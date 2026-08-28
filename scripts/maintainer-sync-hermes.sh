#!/usr/bin/env bash
#
# maintainer-sync-hermes.sh — MAINTAINER-ONLY.
#
# Syncs the canonical source repo (this repo) into a locally installed Hermes
# skill copy. It is NOT an install path for consumers — do not advertise or run it
# from a clone you do not maintain.
#
# Managed (copied) surface:
#   SKILL.md
#   references/            (all files under references/, recursively)
#
# Never copied / touched:
#   .git
#   README.md, LICENSE, SECURITY.md, CHANGELOG.md
#   .github/, scripts/, any repo-only / dev file
#
# Stale removal: files present in the installed managed surface but ABSENT from
# the source managed surface are removed ONLY inside SKILL.md and references/.
#
# Modes:
#   (default)  sync    — copy + remove stale within managed surface
#   --check           — dry run; exit nonzero if any drift would occur
#
# Portable: uses sha256sum if present, else shasum -a 256 (macOS), else openssl.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="${SRC:-"$(cd "$SCRIPT_DIR/.." && pwd)"}"
DST="${DST:-"$HOME/.hermes/skills/trading/kalshi-api-engineering"}"
MODE="sync"
HERMES_BIN="${HERMES_BIN:-hermes}"

hash_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  else
    openssl dgst -sha256 "$1" | sed 's/^.*= //'
  fi
}

usage() {
  cat <<'EOF'
Usage: maintainer-sync-hermes.sh [--check] [--src DIR] [--dst DIR]

  --check   Dry run. Report drift; exit nonzero if sync would change anything.
  --src DIR Canonical source repo (default: parent of this script).
  --dst DIR Installed Hermes skill dir (default: ~/.hermes/skills/trading/kalshi-api-engineering).
  -h,--help Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE="check" ;;
    --src)   SRC="$2"; shift ;;
    --dst)   DST="$2"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [[ ! -f "$SRC/SKILL.md" ]]; then
  echo "ERROR: source SKILL.md missing at: $SRC/SKILL.md" >&2
  exit 1
fi
if [[ ! -d "$SRC/references" ]]; then
  echo "ERROR: source references/ missing at: $SRC/references" >&2
  exit 1
fi

list_managed() {
  local root="$1"
  [[ -f "$root/SKILL.md" ]] && echo "SKILL.md"
  if [[ -d "$root/references" ]]; then
    ( cd "$root/references" && find . -type f | sed 's|^\./|references/|' | sort )
  fi
}

DRIFT=0
SRC_LIST="$(list_managed "$SRC")"
DST_LIST="$(list_managed "$DST" 2>/dev/null || true)"

SRC_SET="$(mktemp)"; printf '%s\n' "$SRC_LIST" > "$SRC_SET"
DST_SET="$(mktemp)"; printf '%s\n' "$DST_LIST" > "$DST_SET"

contains() {
  local s="$1" t="$2"
  [[ "$s" == "$t" ]] || [[ "$s" == *$'\n'"$t"$'\n'* ]] || \
  [[ "$s" == "$t"$'\n'* ]] || [[ "$s" == *$'\n'"$t" ]]
}

ADDED=""; CHANGED=""; REMOVED=""; UNCHANGED=0
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  if [[ ! -f "$DST/$f" ]]; then ADDED="${ADDED:+$ADDED }$f"; DRIFT=1
  elif [[ "$(hash_file "$SRC/$f")" != "$(hash_file "$DST/$f")" ]]; then CHANGED="${CHANGED:+$CHANGED }$f"; DRIFT=1
  else UNCHANGED=$((UNCHANGED+1)); fi
done < "$SRC_SET"

while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  if ! contains "$SRC_LIST" "$f"; then REMOVED="${REMOVED:+$REMOVED }$f"; DRIFT=1; fi
done < "$DST_SET"

echo "Source: $SRC"
echo "Dest:   $DST"
echo "Mode:   $MODE"
echo "Managed surface: SKILL.md, references/"
[[ -n "$ADDED" ]]    && echo "  + added:    $ADDED"
[[ -n "$CHANGED" ]]  && echo "  ~ changed:  $CHANGED"
[[ -n "$REMOVED" ]]  && echo "  - stale:    $REMOVED"
[[ "$UNCHANGED" -gt 0 ]] && echo "  = unchanged: $UNCHANGED file(s)"

if [[ "$MODE" == "check" ]]; then
  rm -f "$SRC_SET" "$DST_SET"
  if [[ $DRIFT -eq 0 ]]; then echo "CHECK OK: no drift."; exit 0
  else echo "CHECK FAILED: drift detected." >&2; exit 1; fi
fi

mkdir -p "$DST/references"
cp -f "$SRC/SKILL.md" "$DST/SKILL.md"
rm -rf "$DST/references"
mkdir -p "$DST/references"
( cd "$SRC/references" && find . -type f -print0 | while IFS= read -r -d '' rf; do
    mkdir -p "$DST/references/$(dirname "$rf")"
    cp -f "$SRC/references/$rf" "$DST/references/$rf"
  done )
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  if ! contains "$SRC_LIST" "$f"; then rm -f "$DST/$f"; fi
done < "$DST_SET"

echo "Synced managed surface to $DST."

DRIFT_AFTER=0
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  if [[ ! -f "$DST/$f" ]] || [[ "$(hash_file "$SRC/$f")" != "$(hash_file "$DST/$f")" ]]; then
    echo "  PARITY FAIL: $f" >&2; DRIFT_AFTER=1
  fi
done < "$SRC_SET"
DEST_AFTER="$(list_managed "$DST")"
printf '%s\n' "$DEST_AFTER" > "$DST_SET"
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  if ! contains "$SRC_LIST" "$f"; then echo "  PARITY FAIL: stale in dest: $f" >&2; DRIFT_AFTER=1; fi
done < "$DST_SET"

for excl in README.md LICENSE SECURITY.md CHANGELOG.md .github scripts; do
  if [[ -e "$DST/$excl" ]]; then echo "  EXCLUSION FAIL: $excl leaked into dest" >&2; DRIFT_AFTER=1; fi
done

rm -f "$SRC_SET" "$DST_SET"
if [[ $DRIFT_AFTER -ne 0 ]]; then echo "SYNC FAILED parity check." >&2; exit 1; fi
echo "Parity OK."

if command -v "$HERMES_BIN" >/dev/null 2>&1; then
  if "$HERMES_BIN" skills list 2>/dev/null | grep -q 'kalshi-api-engineering'; then
    echo "Hermes discovery OK."
  else
    echo "WARN: 'hermes skills list' did not show kalshi-api-engineering." >&2
  fi
else
  echo "WARN: hermes CLI not found at '$HERMES_BIN'; skipping discovery check." >&2
fi
echo "DONE."
