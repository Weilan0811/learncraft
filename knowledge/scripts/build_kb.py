import argparse
import json
import os

from knowledge.engine import kb_engine as kb


def main() -> None:
    parser = argparse.ArgumentParser(
        description="从自有 Markdown 材料建立关键词和向量索引"
    )
    parser.add_argument(
        "--rebuild", action="store_true", help="重新分块并重建当前向量模型的索引"
    )
    args = parser.parse_args()
    chunks = kb.load_all_chunks(force_rebuild=args.rebuild)
    if not chunks:
        parser.exit(1, "未找到可用材料。请先向 knowledge/raw 添加 Markdown 文档。\n")
    filter_junk = os.environ.get("KB_FILTER_JUNK", "1") == "1"
    indexed = kb.indexable_chunks(chunks)
    if not indexed:
        parser.exit(1, "材料没有可索引的正文，请检查内容与结构过滤设置。\n")
    kb.load_bm25_index(indexed).save()
    embedder = kb.get_embedder()
    try:
        kb.ensure_vector_index(indexed, embedder, force_rebuild=args.rebuild)
        metadata = {
            "docs": len({chunk.doc_id for chunk in indexed}),
            "chunks": len(indexed),
            "embedder": type(embedder).__name__,
            "embedder_kind": kb._active_embedder_kind(),
            "collection": kb._active_collection(),
            "embed_dim": kb.EMBED_DIM,
            "junk_filter": filter_junk,
        }
        (kb.KB_INDEX_DIR / "meta.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"索引完成：{metadata['docs']} 篇文档，{metadata['chunks']} 个片段。")
    finally:
        kb.close_qdrant()


if __name__ == "__main__":
    main()
