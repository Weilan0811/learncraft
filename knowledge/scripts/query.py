import argparse
import json
import os

from knowledge.engine import kb_engine as kb


def main() -> None:
    parser = argparse.ArgumentParser(description="查询自建知识库")
    parser.add_argument("text", help="检索问题")
    parser.add_argument(
        "--method", choices=["keyword", "vector", "hybrid", "router"], default="router"
    )
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    chunks = kb.load_all_chunks()
    if os.environ.get("KB_FILTER_JUNK", "1") == "1":
        chunks = [chunk for chunk in chunks if not kb.is_structural_junk(chunk)]
    if not chunks:
        parser.exit(1, "知识库为空，请先添加材料。\n")
    bm25 = kb.load_bm25_index(chunks)
    embedder = kb.get_embedder() if args.method != "keyword" else None
    try:
        results = kb.search(
            args.method, args.text, chunks, bm25, embedder, top_k=args.top_k
        )
        print(
            json.dumps(
                [
                    {
                        "id": chunk.chunk_id,
                        "title": chunk.title,
                        "content": chunk.text,
                        "score": score,
                    }
                    for chunk, score in results
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        kb.close_qdrant()


if __name__ == "__main__":
    main()
