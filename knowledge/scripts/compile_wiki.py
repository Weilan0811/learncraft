"""Compile knowledge/raw pages into the wiki layer (Karpathy LLM Wiki, instantiated per WIKI_SCHEMA.md).

Pipeline (all LLM output is prose only; structured frontmatter is assembled by this script):
  1. summaries   : one raw page -> one wiki summary page (section-level source_refs)
  2. plan        : one LLM call proposes concept/comparison pages across sources (JSON)
  3. build       : concept/comparison pages synthesized from their source docs (doc-level source_refs)
  4. index/log   : rebuild index.md, append log.md entry

Schema: knowledge/WIKI_SCHEMA.md (frontmatter is flat key:value, comma-separated lists --
must stay parseable by kb_engine.parse_frontmatter for the retrieval layer).

Usage (repo root):
    python knowledge/scripts/compile_wiki.py                 # full compile (skips existing)
    python knowledge/scripts/compile_wiki.py --limit 2       # pilot: first 2 summaries only
    python knowledge/scripts/compile_wiki.py --force         # re-compile everything
    python knowledge/scripts/compile_wiki.py --skip-concepts # summaries only (no plan/build)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import httpx

from knowledge.engine.kb_engine import KB_RAW_DIR, parse_frontmatter  # noqa: E402

WIKI_DIR = REPO_ROOT / "knowledge" / "wiki"
CHAT_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL = "qwen-plus"
TEMPERATURE = 0.2
MAX_BODY_CHARS = 12000  # per-source truncation for multi-source synthesis prompts

SYSTEM_SUMMARY = (
    "You are a knowledge editor compiling a dense wiki page from a single source document. "
    "Rules: 1) Keep only verifiable facts, conclusions, parameters, and mechanism descriptions; "
    "drop preamble, extended examples, and derivations. "
    "2) Mirror the source's section structure: reuse the source's section headings VERBATIM as "
    "your '## ' headings -- you may merge or drop sections, but never rewrite a heading. "
    "3) Output markdown; total length 300-600 words. 4) Never invent content not in the source."
)

SYSTEM_PLAN = (
    "You are a wiki architect designing the cross-source layer of an Agent-engineering wiki. "
    "Concept pages must synthesize across 2+ sources; comparison pages must compare things that "
    "actually appear in the source list. Slugs are lowercase-hyphenated."
)

SYSTEM_SYNTH = (
    "You are a knowledge editor synthesizing one wiki page across multiple sources. "
    "Rules: 1) Only verifiable content drawn from the given sources; never invent. "
    "2) Dense prose, prefer tables for comparisons. 3) For cross-source claims you may append a "
    "provenance marker '^[raw/<doc_id>]' at the end of the paragraph. "
    "4) End with a '## Related' section listing at least 2 wikilinks like [[summaries/<doc_id>]] "
    "or [[concepts/<slug>]] -- link ONLY to doc_ids and slugs listed as available."
)


def read_env_key() -> str:
    env_path = REPO_ROOT / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("CONTENT_GENERATOR_BAILIAN_API_KEY="):
            return line.partition("=")[2].strip()
    raise RuntimeError("CONTENT_GENERATOR_BAILIAN_API_KEY not found in .env")


class LLM:
    """Thin chat-completions wrapper with usage accounting."""

    def __init__(self, key: str) -> None:
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        )
        self.tokens_in = 0
        self.tokens_out = 0

    def chat(self, system: str, user: str) -> str:
        resp = self.client.post(
            CHAT_URL,
            json={
                "model": MODEL,
                "temperature": TEMPERATURE,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            },
            timeout=240.0,
        )
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage") or {}
        self.tokens_in += usage.get("prompt_tokens", 0)
        self.tokens_out += usage.get("completion_tokens", 0)
        return data["choices"][0]["message"]["content"].strip()


def frontmatter(kind: str, title: str, tags: str, sources: list[str], refs: list[str], summary: str) -> str:
    today = date.today().isoformat()
    return (
        "---\n"
        f"title: {title}\n"
        f"type: {kind}\n"
        f"tags: {tags}\n"
        f"sources: {','.join(sources)}\n"
        f"source_refs: {','.join(refs)}\n"
        f"summary: {summary}\n"
        f"created: {today}\n"
        f"updated: {today}\n"
        "---\n\n"
    )


def _norm_tokens(s: str) -> set[str]:
    return set(re.sub(r"[^a-z0-9 ]+", " ", s.lower()).split())


def section_anchors(wiki_body: str, raw_body: str, doc_id: str) -> list[str]:
    """Map wiki-kept '## ' sections back to raw sections -> doc_id#Section refs (schema 4.4).

    Matching ladder: verbatim -> normalized-equal -> token overlap >= 0.5 -> fallback '#intro'.
    """
    raw_sections = [s.strip() for s in re.findall(r"^#{2,3}\s+(.+)$", raw_body, re.M)]
    raw_tokens = [_norm_tokens(s) for s in raw_sections]
    refs: list[str] = []
    for sec in re.findall(r"^#{2,3}\s+(.+)$", wiki_body, re.M):
        sec = sec.strip()
        sec_tokens = _norm_tokens(sec)
        match = next((rs for rs, rt in zip(raw_sections, raw_tokens) if rs == sec or rt == sec_tokens), None)
        if match is None and sec_tokens:
            best, best_score = None, 0.0
            for rs, rt in zip(raw_sections, raw_tokens):
                if not rt:
                    continue
                overlap = len(sec_tokens & rt) / max(1, min(len(sec_tokens), len(rt)))
                if overlap > best_score:
                    best, best_score = rs, overlap
            if best_score >= 0.5:
                match = best
        refs.append(f"{doc_id}#{match if match else 'intro'}")
    return refs or [f"{doc_id}#intro"]


def split_summary_line(content: str) -> tuple[str, str]:
    """Extract 'SUMMARY_LINE: ...' -> (one-line summary, body). Fallback: first sentence."""
    m = re.match(r"SUMMARY_LINE:\s*(.+?)\s*\n-{3,}\s*\n(.*)", content, re.S)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    first_line = next((ln for ln in content.splitlines() if ln.strip()), "")
    return first_line.lstrip("# ").strip(), content


def distill_summaries(llm: LLM, force: bool, limit: int) -> int:
    out_dir = WIKI_DIR / "summaries"
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = sorted(KB_RAW_DIR.glob("*.md"))
    if limit:
        pages = pages[:limit]
    done = skipped = failed = 0
    for path in pages:
        out = out_dir / path.name
        if out.exists() and not force:
            skipped += 1
            continue
        try:
            meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            title = meta.get("title") or path.stem
            topic = meta.get("topic", "general")
            user = (
                "First line must be exactly 'SUMMARY_LINE: <one-sentence summary for the wiki index>'. "
                f"Then '---' alone on a line, then the wiki page body (markdown, no frontmatter).\n\n"
                f"# {title}\n\n{body[:24000]}"
            )
            content = llm.chat(SYSTEM_SUMMARY, user)
            summary_line, wiki_body = split_summary_line(content)
            refs = section_anchors(wiki_body, body, path.stem)
            fm = frontmatter("summary", title, topic, [path.stem], refs, summary_line)
            out.write_text(fm + wiki_body + "\n", encoding="utf-8")
            print(f"OK  summary {path.stem} ({len(wiki_body)} chars, {len(refs)} refs)")
            done += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERR summary {path.stem}: {type(exc).__name__}: {str(exc)[:120]}")
            failed += 1
    print(f"summaries: {done} compiled, {skipped} skipped, {failed} failed")
    return failed


def sanitize_slug(slug: str) -> str:
    slug = slug.strip().lower().replace("_", "-")
    return re.sub(r"[^a-z0-9-]+", "-", slug).strip("-") or "untitled"


def parse_plan(content: str) -> list[dict]:
    m = re.search(r"\[.*\]", content, re.S)
    if not m:
        raise ValueError("plan: no JSON array found in response")
    return json.loads(m.group(0))


def plan_pages(llm: LLM) -> list[dict]:
    rows = []
    for path in sorted(KB_RAW_DIR.glob("*.md")):
        meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        rows.append(f"{path.stem} | {meta.get('topic', 'general')} | {meta.get('title', path.stem)}")
    user = (
        "Below is the source list of an Agent-engineering knowledge base (doc_id | topic | title).\n"
        "Propose 5-7 concept pages and 1-2 comparison pages that synthesize ACROSS these sources. "
        "Each page must draw on 2+ sources. Respond with ONLY a JSON array, items:\n"
        '{"kind":"concept"|"comparison","slug":"lowercase-hyphenated","title":"...",'
        '"summary":"one sentence for the wiki index","tags":"comma,separated","doc_ids":["doc_id",...]}\n\n'
        "SOURCE LIST:\n" + "\n".join(rows)
    )
    plan = parse_plan(llm.chat(SYSTEM_PLAN, user))
    for item in plan:
        item["slug"] = sanitize_slug(item.get("slug", ""))
        item["doc_ids"] = [d for d in item.get("doc_ids", []) if (KB_RAW_DIR / f"{d}.md").exists()]
        if item["kind"] not in ("concept", "comparison") or len(item["doc_ids"]) < 2:
            item["_invalid"] = True
    valid = [p for p in plan if not p.get("_invalid")]
    print(f"plan: {len(valid)} pages proposed ({sum(p['kind'] == 'concept' for p in valid)} concepts, "
          f"{sum(p['kind'] == 'comparison' for p in valid)} comparisons)")
    return valid


def synthesize_pages(llm: LLM, plan: list[dict], force: bool) -> int:
    known_slugs = [p["slug"] for p in plan]
    failed = 0
    for page in plan:
        kind_dir = WIKI_DIR / f"{page['kind']}s"
        kind_dir.mkdir(parents=True, exist_ok=True)
        out = kind_dir / f"{page['slug']}.md"
        if out.exists() and not force:
            continue
        try:
            blocks = []
            for doc_id in page["doc_ids"]:
                path = KB_RAW_DIR / f"{doc_id}.md"
                meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
                blocks.append(f"===== {doc_id} ({meta.get('title', doc_id)}) =====\n{body[:MAX_BODY_CHARS]}")
            available = ", ".join(f"summaries/{d}" for d in page["doc_ids"]) + "; " + \
                ", ".join(f"concepts/{s}" for s in known_slugs if s != page["slug"])
            if page["kind"] == "comparison":
                structure = "Use a markdown table for the comparison dimensions, then a '## Verdict' section."
            else:
                structure = ("Sections: '## Definition', '## Key Mechanisms', "
                             "'## Cross-source Consensus & Disagreements', '## Open Questions'.")
            user = (
                f"Page slug: {page['slug']}. Task: {page['summary']}\n"
                f"{structure}\n"
                f"Available link targets (use these exact paths): {available}\n\n" + "\n\n".join(blocks)
            )
            content = llm.chat(SYSTEM_SYNTH, user)
            refs = list(page["doc_ids"])  # doc-level anchoring per schema 4.4
            fm = frontmatter(page["kind"], page["title"], page["tags"], page["doc_ids"], refs, page["summary"])
            out.write_text(fm + content + "\n", encoding="utf-8")
            print(f"OK  {page['kind']} {page['slug']} ({len(content)} chars, {len(refs)} sources)")
        except Exception as exc:  # noqa: BLE001
            print(f"ERR {page['kind']} {page['slug']}: {type(exc).__name__}: {str(exc)[:120]}")
            failed += 1
    return failed


def rebuild_index() -> int:
    sections: dict[str, list[str]] = {"summary": [], "concept": [], "comparison": []}
    total = 0
    for sub in ("summaries", "concepts", "comparisons"):
        for path in sorted((WIKI_DIR / sub).glob("*.md")):
            meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
            ptype = meta.get("type", sub.rstrip("s"))
            rel = f"{sub}/{path.stem}"
            sections.setdefault(ptype, []).append(f"- [[{rel}|{meta.get('title', path.stem)}]] — {meta.get('summary', '')}")
            total += 1
    lines = [
        "# Index — Agent Engineering Knowledge Wiki",
        "",
        "> Compiled wiki layer over knowledge/raw. One line per page: wikilink + one-sentence summary. Read this first.",
        "",
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Total pages: {total}",
        "",
    ]
    labels = {"summary": "Summaries", "concept": "Concepts", "comparison": "Comparisons"}
    for ptype, label in labels.items():
        lines.append(f"## {label}")
        lines.append("")
        lines.extend(sections.get(ptype, ["_(none)_"]))
        lines.append("")
    (WIKI_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")
    return total


def append_log(note: str) -> None:
    log = WIKI_DIR / "log.md"
    if not log.exists():
        log.write_text("# Wiki Log\n\n> Append-only record of wiki operations.\n\n", encoding="utf-8")
    with log.open("a", encoding="utf-8") as f:
        f.write(f"## [{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="compile only first N summaries (pilot)")
    parser.add_argument("--force", action="store_true", help="re-compile existing pages")
    parser.add_argument("--skip-concepts", action="store_true", help="summaries only")
    args = parser.parse_args()

    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    llm = LLM(read_env_key())

    failed = distill_summaries(llm, args.force, args.limit)

    n_concepts = n_comparisons = 0
    if not args.skip_concepts:
        plan = plan_pages(llm)
        failed += synthesize_pages(llm, plan, args.force)
        n_concepts = sum(p["kind"] == "concept" for p in plan)
        n_comparisons = sum(p["kind"] == "comparison" for p in plan)

    total = rebuild_index()
    append_log(f"compile | summaries={args.limit or 21} concepts={n_concepts} "
               f"comparisons={n_comparisons} index_pages={total} (model={MODEL})")
    print(f"\nindex rebuilt: {total} pages; log appended")
    print(f"token usage: in={llm.tokens_in}, out={llm.tokens_out}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
