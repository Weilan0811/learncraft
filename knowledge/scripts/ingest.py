from __future__ import annotations

import argparse
import json
import shutil
import time
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

import sys

sys.path.insert(0, str(REPO_ROOT))

from knowledge.engine import kb_engine as kb


# --- lint gates (mechanical, zero-LLM; ingest fails closed on any gate) ------


def lint_frontmatter(meta: dict[str, str]) -> list[str]:
    """G1: required fields present and meaningful."""
    problems = []
    if not meta.get("title", "").strip():
        problems.append("G1 fail: frontmatter 'title' is required")
    if not meta.get("topic", "").strip():
        problems.append(
            "G1 warn-fail: frontmatter 'topic' is required (use 'general' if unsure)"
        )
    return problems


def lint_chunk_ids(
    new_chunks: list[kb.Chunk], existing_ids: set[str], doc_id: str
) -> list[str]:
    """G2: chunk_id conflicts. Same-doc overlap = legitimate re-ingest (overwrite);
    cross-doc collision is impossible by construction (doc_id is in the id) but
    is still checked defensively."""
    problems = []
    new_ids = {c.chunk_id for c in new_chunks}
    foreign = new_ids & {i for i in existing_ids if not i.startswith(f"{doc_id}::")}
    if foreign:
        problems.append(
            f"G2 fail: chunk_id collision with other docs: {sorted(foreign)[:3]}"
        )
    return problems


def lint_index_parity(filtered_chunks: list[kb.Chunk], collection: str) -> list[str]:
    """G3: after sync, the three stores must agree on the filtered-corpus size."""
    problems = []
    client = kb.get_qdrant()
    q_count = client.count(collection, exact=True).count
    bm25_n = _bm25_size()
    if q_count != len(filtered_chunks):
        problems.append(
            f"G3 fail: qdrant count {q_count} != filtered chunks {len(filtered_chunks)}"
        )
    if bm25_n is not None and bm25_n != len(filtered_chunks):
        problems.append(
            f"G3 fail: bm25 corpus {bm25_n} != filtered chunks {len(filtered_chunks)}"
        )
    return problems


def _bm25_size() -> int | None:
    p = kb.KB_INDEX_DIR / "bm25.pkl"
    if not p.exists():
        return None
    import pickle

    with p.open("rb") as f:
        data = pickle.load(f)
    return len(data["doc_ids"])


# --- core operations (importable, so experiments run in-process) -------------


def _append_cache(chunks: list[kb.Chunk]) -> None:
    """Append chunk lines to chunks.jsonl, preserving the no-trailing-newline
    convention of load_all_chunks so a later retract can restore the file
    byte-identically."""
    cache = kb.KB_INDEX_DIR / "chunks.jsonl"
    cache.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(asdict(c), ensure_ascii=False) for c in chunks]
    if cache.exists():
        raw = cache.read_text(encoding="utf-8")
        if raw.strip():
            if not raw.endswith("\n"):
                raw += "\n"
            raw += "\n".join(lines)
        else:
            raw = "\n".join(lines)
        cache.write_text(raw, encoding="utf-8")
    else:
        cache.write_text("\n".join(lines), encoding="utf-8")


def _rewrite_cache_without(doc_id: str) -> None:
    cache = kb.KB_INDEX_DIR / "chunks.jsonl"
    kept = [
        json.dumps(asdict(c), ensure_ascii=False)
        for c in kb.load_all_chunks()
        if c.doc_id != doc_id
    ]
    cache.write_text("\n".join(kept), encoding="utf-8")


def _log(entry: dict) -> None:
    log_path = kb.KB_INDEX_DIR / "ingest_log.jsonl"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), **entry}, ensure_ascii=False
            )
            + "\n"
        )


def _sync_meta(filtered_all: list[kb.Chunk]) -> None:
    meta_path = kb.KB_INDEX_DIR / "meta.json"
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["docs"] = len({c.doc_id for c in filtered_all})
    meta["chunks"] = len(filtered_all)
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def ingest_file(file: Path, dry_run: bool = False) -> dict:
    """Full mechanical ingest loop for one markdown file. Returns a summary
    dict; raises RuntimeError on any lint gate failure (fail closed)."""
    t0 = time.perf_counter()
    file = Path(file).resolve()
    target = file if file.parent == kb.KB_RAW_DIR else kb.KB_RAW_DIR / file.name
    if file.parent != kb.KB_RAW_DIR:
        kb.KB_RAW_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)
    doc_id = target.stem

    meta, _body = kb.parse_frontmatter(target.read_text(encoding="utf-8"))
    new_chunks = kb.chunk_markdown(target)
    if not new_chunks:
        raise RuntimeError(f"ingest aborted: {target.name} produced zero chunks")

    # -- lint G1/G2 (fail closed)
    problems = lint_frontmatter(meta) + lint_chunk_ids(
        new_chunks, {c.chunk_id for c in kb.load_all_chunks()}, doc_id
    )
    if problems:
        raise RuntimeError("ingest aborted by lint gates:\n  " + "\n  ".join(problems))

    junk = [c for c in new_chunks if kb.is_structural_junk(c)]
    indexable = [c for c in new_chunks if not kb.is_structural_junk(c)]

    if dry_run:
        return {
            "doc_id": doc_id,
            "chunks": len(new_chunks),
            "junk": len(junk),
            "dry_run": True,
            "lint": "PASS",
        }

    embedder = kb.get_embedder()
    vectors = embedder.embed([f"{c.title} | {c.section} | {c.text}" for c in indexable])

    # 向量生成成功后再修改缓存，避免服务请求失败时留下半更新的数据。
    _rewrite_cache_without(doc_id)
    _append_cache(new_chunks)

    # -- index sync
    filtered_all = [c for c in kb.load_all_chunks() if not kb.is_structural_junk(c)]
    bm25 = kb.BM25Index(filtered_all)
    bm25.save()

    collection = kb._active_collection()
    client = kb.get_qdrant()
    from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

    if not client.collection_exists(collection):
        kb.ensure_vector_index([], embedder, collection=collection)
    client.delete(
        collection,
        points_selector=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        ),
    )
    points = [
        PointStruct(
            id=kb.chunk_point_id(c.chunk_id),
            vector=vec,
            payload={
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "title": c.title,
                "topic": c.topic,
                "scope": c.scope,
            },
        )
        for c, vec in zip(indexable, vectors)
    ]
    for start in range(0, len(points), 100):
        client.upsert(collection, points[start : start + 100])

    # -- lint G3 (post-sync parity)
    problems = lint_index_parity(filtered_all, collection)
    if problems:
        raise RuntimeError(
            "ingest sync failed parity check (run build_kb.py --rebuild to recover):\n  "
            + "\n  ".join(problems)
        )

    _sync_meta(filtered_all)
    summary = {
        "action": "ingest",
        "doc_id": doc_id,
        "file": str(target.relative_to(REPO_ROOT)),
        "chunks_total": len(new_chunks),
        "chunks_indexed": len(indexable),
        "junk_skipped": len(junk),
        "qdrant_points": len(points),
        "lint": "PASS",
        "seconds": round(time.perf_counter() - t0, 1),
    }
    _log(summary)
    return summary


def retract_doc(doc_id: str, dry_run: bool = False) -> dict:
    """Retract a doc from raw + cache + both indexes. The raw md is moved to
    storage/kb/retracted/ (reversible), not deleted."""
    t0 = time.perf_counter()
    all_chunks = kb.load_all_chunks()
    doc_chunks = [c for c in all_chunks if c.doc_id == doc_id]
    if not doc_chunks:
        raise RuntimeError(
            f"retract aborted: doc_id {doc_id!r} has no chunks in the cache"
        )

    if dry_run:
        return {"doc_id": doc_id, "chunks": len(doc_chunks), "dry_run": True}

    # 1. raw md -> retracted/ (reversible safety net)
    src = kb.KB_RAW_DIR / f"{doc_id}.md"
    if src.exists():
        q_dir = kb.KB_INDEX_DIR / "retracted"
        q_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(q_dir / f"{doc_id}.md"))

    # 2. cache rewrite
    _rewrite_cache_without(doc_id)

    # 3. index sync
    filtered_all = [c for c in kb.load_all_chunks() if not kb.is_structural_junk(c)]
    bm25 = kb.BM25Index(filtered_all)
    bm25.save()

    from qdrant_client.models import FieldCondition, Filter, MatchValue

    collection = kb._active_collection()
    client = kb.get_qdrant()
    client.delete(
        collection,
        points_selector=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        ),
    )

    problems = lint_index_parity(filtered_all, collection)
    if problems:
        raise RuntimeError(
            "retract sync failed parity check (run build_kb.py --rebuild to recover):\n  "
            + "\n  ".join(problems)
        )

    _sync_meta(filtered_all)
    summary = {
        "action": "retract",
        "doc_id": doc_id,
        "chunks_removed": len(doc_chunks),
        "lint": "PASS",
        "seconds": round(time.perf_counter() - t0, 1),
    }
    _log(summary)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(
        description="KB dynamic ingest / retract (mechanical spine)"
    )
    ap.add_argument(
        "--file", help="markdown file to ingest (copied into knowledge/raw/ if outside)"
    )
    ap.add_argument("--retract", help="doc_id to retract")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.file and not args.retract:
        ap.error("provide --file <md> or --retract <doc_id>")
    if args.file:
        summary = ingest_file(Path(args.file), dry_run=args.dry_run)
    else:
        summary = retract_doc(args.retract, dry_run=args.dry_run)
    kb.close_qdrant()  # CLI path: flush local-mode persistence before exit
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
