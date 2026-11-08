"""Self-hosted knowledge-base service wired into the generation pipeline.

Implements the RAGService contract on top of knowledge/raw/ (BM25 + dense
vectors fused with query-type-routed weighted RRF, see kb_engine). Replaces
the external lab KB API whose outage used to starve the whole pipeline.
"""

from __future__ import annotations

from app.schemas.request import ContentGenerationRequest
from app.schemas.state import RetrievedChunk
from app.services import kb_engine as kb
from app.services.rag_service import RAGService


class LocalKBService(RAGService):
    def __init__(self, top_k: int = 5, method: str = "router", api_key: str = "") -> None:
        self.top_k = top_k
        self.method = method
        self.api_key = api_key
        self._chunks: list[kb.Chunk] | None = None
        self._bm25: kb.BM25Index | None = None
        self._embedder: kb.BailianEmbedder | None = None
        self.last_diagnostics: dict[str, object] = {}

    def _ensure_loaded(self) -> None:
        if self._bm25 is None:
            self._chunks = kb.load_all_chunks()
            self._bm25 = kb.load_bm25_index(self._chunks)
            self._embedder = kb.BailianEmbedder(api_key=self.api_key)

    def retrieve(self, request: ContentGenerationRequest, stage: str, section_hint: str | None = None) -> list[RetrievedChunk]:
        self._ensure_loaded()
        assert self._chunks is not None and self._bm25 is not None and self._embedder is not None
        parts = [request.topic, request.user_prompt, stage]
        if request.system_prompt:
            parts.append(request.system_prompt)
        if section_hint:
            parts.append(section_hint)
        query = "\n".join(part for part in parts if part)
        try:
            results = kb.search(self.method, query, self._chunks, self._bm25, self._embedder, top_k=self.top_k)
        except Exception as exc:
            self.last_diagnostics = {"status": "failed", "error_type": type(exc).__name__, "error_message": str(exc), "stage": stage}
            return []
        self.last_diagnostics = {
            "status": "ok",
            "stage": stage,
            "method": self.method,
            "query_preview": query[:300],
            "chunk_count": len(results),
            "chunk_ids": [c.chunk_id for c, _ in results],
        }
        return [
            RetrievedChunk(
                id=chunk.chunk_id,
                source_id=chunk.doc_id,
                source_title=chunk.title,
                content=chunk.text,
                score=float(score),
                metadata={
                    "stage": stage,
                    "section_hint": section_hint or "",
                    "topic": chunk.topic,
                    "section": chunk.section,
                    "source_url": chunk.source_url,
                },
            )
            for chunk, score in results
        ]
