import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from knowledge.engine import kb_engine as kb


def build_index(output_root: Path) -> dict:
    original_index, original_qdrant = kb.KB_INDEX_DIR, kb.QDRANT_DIR
    kb.close_qdrant()
    kb.KB_INDEX_DIR, kb.QDRANT_DIR = output_root / "kb", output_root / "qdrant_kb"
    try:
        chunks = kb.load_all_chunks(force_rebuild=True)
        indexed = kb.indexable_chunks(chunks)
        if not indexed:
            raise ValueError("未找到可索引正文，请检查 knowledge/raw 和过滤设置。")
        if len({chunk.chunk_id for chunk in indexed}) != len(indexed):
            raise ValueError("新索引包含重复片段编号，停止构建。")
        kb.load_bm25_index(indexed).save()
        embedder = kb.get_embedder()
        kb.ensure_vector_index(indexed, embedder, force_rebuild=True)
        metadata = {
            "docs": len({chunk.doc_id for chunk in indexed}), "chunks": len(indexed),
            "embedder": type(embedder).__name__, "embedder_kind": kb._active_embedder_kind(),
            "collection": kb._active_collection(), "embed_dim": kb.EMBED_DIM,
            "junk_filter": os.environ.get("KB_FILTER_JUNK", "1") == "1",
            "chunk_id_version": kb.CHUNK_ID_VERSION,
            "built_at": datetime.now(timezone.utc).isoformat(),
        }
        (kb.KB_INDEX_DIR / "meta.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return metadata
    finally:
        kb.close_qdrant()
        kb.KB_INDEX_DIR, kb.QDRANT_DIR = original_index, original_qdrant


def activate_index(output_root: Path) -> Path:
    kb.close_qdrant()
    storage = kb.KB_INDEX_DIR.parent
    backup = Path(tempfile.mkdtemp(prefix="kb-backup-", dir=storage))
    destinations = {"kb": kb.KB_INDEX_DIR, "qdrant_kb": kb.QDRANT_DIR}
    backed_up, installed = [], []
    try:
        for name, destination in destinations.items():
            if destination.exists():
                destination.rename(backup / name)
                backed_up.append(name)
            (output_root / name).rename(destination)
            installed.append(name)
    except Exception:
        for name in reversed(installed):
            destinations[name].rename(output_root / name)
        for name in reversed(backed_up):
            (backup / name).rename(destinations[name])
        raise
    return backup


def main() -> None:
    parser = argparse.ArgumentParser(
        description="从自有 Markdown 材料建立关键词和向量索引"
    )
    parser.add_argument(
        "--rebuild", action="store_true", help="重新分块并重建当前向量模型的索引"
    )
    parser.add_argument("--output-dir", type=Path, help="构建到新的独立目录，不替换当前索引")
    args = parser.parse_args()
    metadata_path = kb.KB_INDEX_DIR / "meta.json"
    if args.output_dir is None and not args.rebuild and metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("chunk_id_version") == kb.CHUNK_ID_VERSION and metadata.get("embedder_kind") == kb._active_embedder_kind():
            try:
                count = kb.get_qdrant().count(kb._active_collection(), exact=True).count
                if count != metadata["chunks"]:
                    raise ValueError("索引数量不一致，请使用 --rebuild 重建。")
                print(f"索引已存在：{metadata['docs']} 篇文档，{count} 个片段；使用 --rebuild 可重建。")
                return
            finally:
                kb.close_qdrant()
    if args.output_dir is not None:
        output = args.output_dir.resolve()
        if output.exists() and any(output.iterdir()):
            parser.error("输出目录必须为空，旧索引不作为构建目录。")
        output.mkdir(parents=True, exist_ok=True)
    else:
        kb.KB_INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix="kb-build-", dir=kb.KB_INDEX_DIR.parent))
    metadata = build_index(output)
    if args.output_dir is None:
        backup = activate_index(output)
        output.rmdir()
        print(f"旧索引备份：{backup}")
    print(f"索引完成：{metadata['docs']} 篇文档，{metadata['chunks']} 个片段。")


if __name__ == "__main__":
    main()
