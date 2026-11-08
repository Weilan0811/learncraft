"""Build the local KB indexes from knowledge/raw/*.md.

Produces (all derivable, safe to delete and rebuild):
- storage/kb/chunks.jsonl   : all chunks with metadata
- storage/kb/bm25.pkl       : BM25 tokenized corpus
- storage/qdrant_kb/        : Qdrant local collection with dense vectors

Usage (repo root):
    python knowledge/scripts/build_kb.py            # incremental (reuses caches)
    python knowledge/scripts/build_kb.py --rebuild  # force rebuild everything
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services import kb_engine as kb  # noqa: E402


def read_env_key() -> str:
    env_path = REPO_ROOT / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("CONTENT_GENERATOR_BAILIAN_API_KEY="):
            return line.partition("=")[2].strip()
    return ""


def main() -> None:
    force = "--rebuild" in sys.argv
    chunks = kb.load_all_chunks(force_rebuild=force)
    if not chunks:
        print("No chunks produced. Check knowledge/raw/*.md")
        sys.exit(1)

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

    print("building vector index (Bailian text-embedding-v3) ...")
    embedder = kb.BailianEmbedder(api_key=read_env_key())
    kb.ensure_vector_index(chunks, embedder, force_rebuild=force)

    meta = {
        "docs": len(docs),
        "chunks": len(chunks),
        "topics": topics,
        "embed_model": kb.EMBED_MODEL,
        "embed_dim": kb.EMBED_DIM,
    }
    (kb.KB_INDEX_DIR / "meta.json").write_text(
        __import__("json").dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("done. indexes at storage/kb and storage/qdrant_kb")


if __name__ == "__main__":
    main()
