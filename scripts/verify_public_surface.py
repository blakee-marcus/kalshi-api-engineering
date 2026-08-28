#!/usr/bin/env python3
"""Verify the public surface of the kalshi-api-engineering skill.

Run by .github/workflows/verify.yml on every push. Fails (exit nonzero) on:
  - malformed SKILL.md frontmatter
  - missing required files
  - absolute personal paths (home-dir absolute paths, internal project dirs)
  - obvious credential material
  - broken local reference links (in SKILL.md / README.md)
  - project-specific bot leakage
  - reference pages without an official source URL
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAIL = []


def err(msg: str) -> None:
    FAIL.append(msg)
    print(f"FAIL: {msg}")


def ok(msg: str) -> None:
    print(f"ok:   {msg}")


def check_frontmatter() -> None:
    skill = ROOT / "SKILL.md"
    if not skill.exists():
        err("SKILL.md missing")
        return
    text = skill.read_text()
    if not text.startswith("---"):
        err("SKILL.md missing leading frontmatter delimiter")
        return
    end = text.find("\n---", 3)
    if end == -1:
        err("SKILL.md frontmatter not closed")
        return
    fm = text[3:end]
    for key in ["name:", "description:", "license:", "author:", "homepage:", "version:"]:
        if key not in fm:
            err(f"SKILL.md frontmatter missing '{key}'")
    ok("SKILL.md frontmatter present")


def check_required_files() -> None:
    for f in ["SKILL.md", "README.md", "LICENSE", "SECURITY.md", "CHANGELOG.md"]:
        if not (ROOT / f).exists():
            err(f"required file missing: {f}")
        else:
            ok(f"required file present: {f}")
    refs = ROOT / "references"
    if not refs.is_dir():
        err("references/ directory missing")
    elif not any(refs.iterdir()):
        err("references/ is empty")


PERSONAL = re.compile(r"/Users/[^ \t\n\"'`]+|~/" + r"\.hermes/projects")
BOT = re.compile(r"kashibot|kashi_bot|kashibotruntime".replace("kashibot", "KashiBot"), re.IGNORECASE)
CRED = re.compile(
    r"(?i)(api[_-]?key|secret|private[_-]?key|token|passphrase)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}",
)
OBS = re.compile(r"obsidian", re.IGNORECASE)
TG = re.compile(r"telegram", re.IGNORECASE)


def scan_file(p: Path) -> None:
    text = p.read_text(errors="replace")
    rel = p.relative_to(ROOT)
    if PERSONAL.search(text):
        err(f"{rel}: absolute personal path (home-dir or internal project dir)")
    if BOT.search(text):
        err(f"{rel}: bot-specific identifier leakage")
    if CRED.search(text):
        err(f"{rel}: possible credential material")
    if OBS.search(text):
        err(f"{rel}: personal-note reference (internal)")
    if TG.search(text):
        err(f"{rel}: activation-channel reference (internal)")


def check_no_state_changing_requests() -> None:
    """Fail if README.md / SKILL.md embed an executable state-changing request.

    The skill is read-only by design: any POST/PUT/PATCH/DELETE against a live
    (production or demo) Kalshi endpoint, or a cancel-all pattern, contradicts the
    stated safety boundary and must not ship.
    """
    state_re = re.compile(
        r"requests\.(post|put|patch|delete)\s*\(", re.IGNORECASE)
    cancel_all = re.compile(r"cancel[\s_-]?all", re.IGNORECASE)
    for fname in ["README.md", "SKILL.md"]:
        p = ROOT / fname
        if not p.exists():
            continue
        rel = fname
        for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            if state_re.search(line):
                err(f"{rel}:{i}: executable state-changing request ({state_re.search(line).group(0)})")
            if cancel_all.search(line):
                err(f"{rel}:{i}: cancel-all pattern present")
    if not any(f.startswith("FAIL") for f in FAIL):
        ok("no embedded state-changing requests in README.md / SKILL.md")


def check_patterns() -> None:
    for p in [ROOT / "SKILL.md", ROOT / "README.md", ROOT / "SECURITY.md"]:
        if p.exists():
            scan_file(p)
    refs = ROOT / "references"
    if refs.is_dir():
        for p in sorted(refs.glob("*.md")):
            scan_file(p)
    if not FAIL:
        ok("no personal paths / bot identifiers / credentials / notes / channel leakage")


def check_local_links() -> None:
    refs = ROOT / "references"
    ref_names = {p.name for p in refs.glob("*.md")} if refs.is_dir() else set()
    link_re = re.compile(r"`?(references/[A-Za-z0-9_\-]+\.md)`?")
    for p in [ROOT / "SKILL.md", ROOT / "README.md"]:
        if not p.exists():
            continue
        rel = p.relative_to(ROOT)
        for m in link_re.finditer(p.read_text()):
            if m.group(1).split("/", 1)[1] not in ref_names:
                err(f"{rel}: links to missing reference: {m.group(1)}")
    if not any(f.startswith("FAIL") for f in FAIL):
        ok("local reference links resolve")


def check_source_urls() -> None:
    refs = ROOT / "references"
    if not refs.is_dir():
        return
    missing = [p.name for p in sorted(refs.glob("*.md"))
               if "docs.kalshi.com" not in "\n".join(p.read_text(errors="replace").splitlines()[:15])
               and "kalshi.com" not in "\n".join(p.read_text(errors="replace").splitlines()[:15])]
    if missing:
        err(f"reference pages without an official source URL: {', '.join(missing)}")
    else:
        ok("every reference page cites an official source URL")


def check_source_manifest() -> None:
    """Fail if a reference page lacks an official source URL + ingest date."""
    refs = ROOT / "references"
    if not refs.is_dir():
        return
    for p in sorted(refs.glob("*.md")):
        if p.name in {"api-documentation-index.md"}:
            continue
        text = p.read_text(errors="replace")
        head = "\n".join(text.splitlines()[:12])
        if "docs.kalshi.com" not in head and "kalshi.com" not in head:
            err(f"{p.name}: no official source URL in header")
        if "ingest" not in text.lower() and "last ingested" not in text.lower():
            err(f"{p.name}: no ingest date recorded")


def check_routing_links() -> None:
    """SKILL.md command table must link to an existing references/<cmd>.md."""
    skill = ROOT / "SKILL.md"
    if not skill.exists():
        return
    refs = ROOT / "references"
    ref_names = {p.stem for p in refs.glob("*.md")} if refs.is_dir() else set()
    for m in re.finditer(r"\(`([a-z\-]+)\.md`\)", skill.read_text()):
        if m.group(1) not in ref_names:
            err(f"SKILL.md routes to missing playbook: {m.group(1)}.md")


def main() -> int:
    print(f"Verifying public surface at {ROOT}\n")
    check_frontmatter()
    check_required_files()
    check_patterns()
    check_no_state_changing_requests()
    check_local_links()
    check_routing_links()
    check_source_manifest()
    check_source_urls()
    print()
    if FAIL:
        print(f"{len(FAIL)} failure(s).")
        return 1
    print("Public surface clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
