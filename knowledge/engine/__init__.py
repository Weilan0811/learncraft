"""Knowledge retrieval engine (moved out of backend/app/services).

Pure retrieval layer with no dependency on the backend app package:
chunking, BM25 (jieba), Qdrant dense index (Bailian text-embedding), and the
four retrieval strategies compared in the D2 evaluation (keyword / vector /
hybrid-RRF / router).

Consumers:
- ``backend/app/services/local_kb_service.py`` adapts this engine to the
  RAGService contract for the generation pipeline.
- ``knowledge/scripts/build_kb.py`` rebuilds the derivable indexes under
  ``storage/kb`` and ``storage/qdrant_kb`` from ``knowledge/raw/``.
- ``knowledge/scripts/bench_retrieval.py`` runs the recall@k / MRR evaluation.
"""

from knowledge.engine.kb_engine import (
    BailianEmbedder,
    BGEM3Embedder,
    BM25Index,
    Chunk,
    Embedder,
    chunks_from_text,
    cosine_search,
    get_embedder,
    load_all_chunks,
    load_bm25_index,
    parse_frontmatter,
    resolve_bge_model_path,
    search,
    search_vector,
)

__all__ = [
    "BailianEmbedder",
    "BGEM3Embedder",
    "BM25Index",
    "Chunk",
    "Embedder",
    "chunks_from_text",
    "cosine_search",
    "get_embedder",
    "load_all_chunks",
    "load_bm25_index",
    "parse_frontmatter",
    "resolve_bge_model_path",
    "search",
    "search_vector",
]
