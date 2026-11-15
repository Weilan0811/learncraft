"""Mechanical lint for knowledge/wiki (WIKI_SCHEMA.md §6 three checks, zero API cost).

Checks:
  1. dead-links  : every [[path]] in wiki pages (incl. index.md) resolves to an existing file
  2. orphans     : every page under wiki/{summaries,concepts,comparisons}/ is registered in index.md
  3. index-consistency : every index.md wikilink target exists and is registered exactly once

Also prints per-page outbound link counts (schema 4.2 asks concept/comparison pages for >= 2;
mechanical lint reports but does not fail on this -- enforced at human review).

Usage (repo root):
    python knowledge/scripts/lint_wiki.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WIKI_DIR = REPO_ROOT / "knowledge" / "wiki"
PAGE_DIRS = ("summaries", "concepts", "comparisons")

WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")


def extract_links(text: str) -> list[str]:
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(text) if not m.group(1).strip().startswith("#")]


def main() -> int:
    if not WIKI_DIR.exists():
        print("wiki layer missing: knowledge/wiki not found")
        return 1

    pages = sorted(WIKI_DIR.glob("*/*.md")) + sorted(WIKI_DIR.glob("*.md"))
    errors: list[str] = []

    # 1. dead links (all files, incl. index.md / log.md)
    dead = 0
    total_links = 0
    for path in pages:
        for link in extract_links(path.read_text(encoding="utf-8")):
            total_links += 1
            if not (WIKI_DIR / f"{link}.md").exists():
                errors.append(f"dead-link: {path.relative_to(WIKI_DIR)} -> [[{link}]]")
                dead += 1
    print(f"check 1 dead-links: {total_links} links scanned, {dead} dead")

    # 2. orphans: every page registered in index.md
    index_path = WIKI_DIR / "index.md"
    index_links = extract_links(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    index_set = set(index_links)
    registered = 0
    for path in sorted(WIKI_DIR.glob("*/*.md")):
        rel = f"{path.parent.name}/{path.stem}"
        if rel not in index_set:
            errors.append(f"orphan: {rel} not registered in index.md")
        else:
            registered += 1
    total_pages = len(list(WIKI_DIR.glob("*/*.md")))
    print(f"check 2 orphans: {registered}/{total_pages} pages registered")

    # 3. index consistency: every index link resolves + no duplicates
    dupes = len(index_links) - len(index_set)
    unresolved = sum(1 for link in index_links if not (WIKI_DIR / f"{link}.md").exists())
    for link in index_links:
        if not (WIKI_DIR / f"{link}.md").exists():
            errors.append(f"index-consistency: index.md -> [[{link}]] does not resolve")
    if dupes:
        counted: dict[str, int] = {}
        for link in index_links:
            counted[link] = counted.get(link, 0) + 1
        for link, n in counted.items():
            if n > 1:
                errors.append(f"index-consistency: [[{link}]] registered {n} times")
    print(f"check 3 index-consistency: {len(index_links)} entries, {unresolved} unresolved, {dupes} duplicates")

    # info: outbound link counts (concept/comparison pages should have >= 2 per schema 4.2)
    print("\noutbound links per page (concept/comparison should be >= 2):")
    for path in sorted(WIKI_DIR.glob("*/*.md")):
        n = len(extract_links(path.read_text(encoding="utf-8")))
        flag = ""
        if path.parent.name in ("concepts", "comparisons") and n < 2:
            flag = "  <-- WARN: below schema target"
        print(f"  {path.parent.name}/{path.stem}: {n}{flag}")

    if errors:
        print(f"\nFAIL: {len(errors)} lint error(s)")
        for e in errors:
            print(f"  {e}")
        return 1
    print("\nPASS: all mechanical checks clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
