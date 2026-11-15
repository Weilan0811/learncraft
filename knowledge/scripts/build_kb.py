"""Build the local KB indexes from knowledge/raw/*.md.

Produces (all derivable, safe to delete and rebuild):
- storage/kb/chunks.jsonl   : all chunks with metadata (NEVER filtered)
- storage/kb/bm25.pkl       : BM25 tokenized corpus
- storage/qdrant_kb/        : Qdrant local collection with dense vectors

KB_FILTER_JUNK=1 (default 1 since 2026-11-14): structural junk (References/
TOC/LaTeX debris, kb_engine.is_structural_junk) is EXCLUDED from the indexes.
chunks.jsonl and the chunk_id space are never touched, so eval assets (v8
snapshot GT, span offsets) stay valid -- junk present-but-unretrievable is
operationally equivalent to junk absent. Set KB_FILTER_JUNK=0 to build the
pre-cleaning corpus for AB comparison (3.6 report-v8 does exactly that).

Usage (repo root):
    python knowledge/scripts/build_kb.py            # incremental (reuses caches)
    python knowledge/scripts/build_kb.py --rebuild  # force rebuild everything
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

from knowledge.engine import kb_engine as kb


def main() -> None:
    force = "--rebuild" in sys.argv
    filter_junk = os.environ.get("KB_FILTER_JUNK", "1") == "1"
    if force:
        # Nuclear option: wipe qdrant storage dir entirely. Rationale: local-mode
        # delete_collection + create_collection in one process was observed NOT to
        # persist (2026-11-14, unit-4 ingest experiment) -- the old collection kept
        # serving from disk while the rebuild silently collided with it. A clean
        # directory + fresh create is the only path proven to persist correctly.
        import shutil

        if kb.QDRANT_DIR.exists():
            shutil.rmtree(kb.QDRANT_DIR)
            print(f"wiped qdrant storage dir {kb.QDRANT_DIR} for clean rebuild")
    chunks = kb.load_all_chunks(force_rebuild=force)
    if not chunks:
        print("No chunks produced. Check knowledge/raw/*.md")
        sys.exit(1)

    if filter_junk:
        all_n = len(chunks)
        chunks = [c for c in chunks if not kb.is_structural_junk(c)]
        print(f"junk filter ON: {all_n - len(chunks)}/{all_n} structural-junk chunks excluded from INDEXES")
    else:
        print("junk filter OFF: full corpus indexed (pre-cleaning AB round)")

    topics: dict[str, int] = {}
    for c in chunks:
        topics[c.topic] = topics.get(c.topic, 0) + 1
    docs = sorted({c.doc_id for c in chunks})
    print(f"docs: {len(docs)} | chunks: {len(chunks)} | avg chars: {sum(c.char_count for c in chunks) // len(chunks)}")
    for topic, count in sorted(topics.items(), key=lambda x: -x[1]):
        print(f"  topic {topic}: {count} chunks")

    print("building BM25 index ...")
    bm25 = kb.load_bm25_index(chunks, force_rebuild=force)
    bm25.save()

    embedder = kb.get_embedder()
    print(f"building vector index ({type(embedder).__name__}, collection {kb._active_collection()}) ...")
    kb.ensure_vector_index(chunks, embedder, force_rebuild=force)

    print("building wiki parent-layer index (separate collection) ...")
    wiki_chunks = kb.load_wiki_chunks(force_rebuild=force)
    if wiki_chunks:
        kb.ensure_vector_index(wiki_chunks, embedder, force_rebuild=force, collection=kb._active_collection(wiki=True))
        print(f"  wiki layer: {len(wiki_chunks)} chunks from {len({c.doc_id for c in wiki_chunks})} pages")
    else:
        print("  wiki layer empty -- run knowledge/scripts/compile_wiki.py first")

    meta = {
        "docs": len(docs),
        "chunks": len(chunks),
        "topics": topics,
        "embedder": type(embedder).__name__,
        "embedder_kind": kb._active_embedder_kind(),
        "collection": kb._active_collection(),
        "embed_dim": kb.EMBED_DIM,
        "junk_filter": filter_junk,
        "junk_filter_rule": "kb_engine.is_structural_junk v2 (nav link-line mean length < 120)",
    }
    (kb.KB_INDEX_DIR / "meta.json").write_text(
        __import__("json").dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    kb.close_qdrant()  # flush local-mode persistence before exit (see close_qdrant docstring)
    print("done. indexes at storage/kb and storage/qdrant_kb")


if __name__ == "__main__":
    main()
