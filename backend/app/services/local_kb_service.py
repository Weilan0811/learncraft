"""Self-hosted knowledge-base service wired into the generation pipeline.

Implements the RAGService contract on top of knowledge/raw/ (BM25 + dense
vectors fused with query-type-routed weighted RRF, see kb_engine). Replaces
the external lab KB API whose outage used to starve the whole pipeline.

Task attachments (kb_mode): user-supplied materials live in their own
per-task namespace — a throwaway in-memory BM25 index plus on-the-fly cosine
search with content-hash caching. Small namespaces don't justify a shared
index write; a persistent personal KB would move them into the shared
collection behind a scope filter (multi-tenant strategy, see README).
"""

from __future__ import annotations

import hashlib

from app.schemas.request import AttachmentDoc, ContentGenerationRequest
from app.schemas.state import RetrievalStatus, RetrievedChunk
from knowledge.engine import kb_engine as kb
from app.services.rag_service import RAGService, RetrievalResult

# Fused mode: the attached materials are usually written for exactly this
# task, so a modest boost over the platform KB keeps them at the front of
# mixed rankings without drowning platform context entirely.
_FUSED_WEIGHTS = [1.0, 1.3]  # [platform, attachment]


class LocalKBService(RAGService):
    def __init__(self, top_k: int = 5, method: str = "router", api_key: str = "") -> None:
        self.top_k = top_k
        self.method = method
        self.api_key = api_key
        self._chunks: list[kb.Chunk] | None = None
        self._bm25: kb.BM25Index | None = None
        self._embedder: kb.Embedder | None = None
        self.last_diagnostics: dict[str, object] = {}
        # sha256(contextualized text) -> embedding, shared across attachments
        # so the same uploaded material is embedded once per process.
        self._vector_cache: dict[str, list[list[float]]] = {}

    def _ensure_loaded(self, mode: str) -> None:
        if mode != "materials_only" and self._bm25 is None:
            self._chunks = kb.load_all_chunks()
            self._bm25 = kb.load_bm25_index(self._chunks)
        if self.method != "keyword" and self._embedder is None and (mode != "platform" or self._chunks):
            self._embedder = kb.get_embedder(api_key=self.api_key or None)

    def _build_query(self, request: ContentGenerationRequest, stage: str, section_hint: str | None) -> str:
        parts = [request.topic, request.user_prompt, stage]
        if request.system_prompt:
            parts.append(request.system_prompt)
        if section_hint:
            parts.append(section_hint)
        return "\n".join(part for part in parts if part)

    def _attachment_chunks(self, attachments: list[AttachmentDoc]) -> list[kb.Chunk]:
        chunks: list[kb.Chunk] = []
        for att in attachments:
            doc_id = f"att::{att.filename}"
            chunks.extend(
                kb.chunks_from_text(
                    doc_id=doc_id,
                    title=att.filename,
                    text=att.content,
                    topic="attachment",
                    scope="attachment",
                )
            )
        return chunks

    def _search_attachments(self, query: str, attachments: list[AttachmentDoc], top_k: int) -> list[tuple[kb.Chunk, float]]:
        chunks = self._attachment_chunks(attachments)
        if not chunks:
            return []
        # Per-task BM25 (fresh, never persisted) + in-memory cosine search.
        kw = kb.BM25Index(chunks).search(query, top_k=20)
        if self.method == "keyword":
            return kw[:top_k]
        assert self._embedder is not None
        vec = kb.cosine_search(query, chunks, self._embedder, top_k=20, vector_cache=self._vector_cache)
        fused = kb.rrf_fuse([[c.chunk_id for c, _ in kw], [c.chunk_id for c, _ in vec]])
        chunk_by_id = {c.chunk_id: c for c in chunks}
        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(chunk_by_id[cid], score) for cid, score in ranked if cid in chunk_by_id]

    def retrieve(self, request: ContentGenerationRequest, stage: str, section_hint: str | None = None) -> RetrievalResult:
        query = self._build_query(request, stage, section_hint)
        mode = request.kb_mode
        attachments = list(request.attachments)
        try:
            self._ensure_loaded(mode)
            if mode == "materials_only":
                results = self._search_attachments(query, attachments, top_k=self.top_k)
            elif mode == "fused":
                platform = kb.search(self.method, query, self._chunks, self._bm25, self._embedder, top_k=self.top_k) if self._chunks else []
                attached = self._search_attachments(query, attachments, top_k=self.top_k)
                fused = kb.rrf_fuse(
                    [[c.chunk_id for c, _ in platform], [c.chunk_id for c, _ in attached]],
                    weights=_FUSED_WEIGHTS,
                )
                chunk_by_id = {c.chunk_id: c for c in [*self._chunks, *self._attachment_chunks(attachments)]}
                ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[: self.top_k]
                results = [(chunk_by_id[cid], score) for cid, score in ranked if cid in chunk_by_id]
            else:
                results = kb.search(self.method, query, self._chunks, self._bm25, self._embedder, top_k=self.top_k) if self._chunks else []
        except Exception as exc:
            self.last_diagnostics = {
                "status": "failed",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "stage": stage,
                "kb_mode": mode,
            }
            return RetrievalResult(
                chunks=[],
                status=RetrievalStatus(state="failed", chunk_count=0, message=f"本地知识库检索失败：{exc}"),
            )
        self.last_diagnostics = {
            "status": "ok",
            "stage": stage,
            "method": self.method,
            "kb_mode": mode,
            "query_preview": query[:300],
            "chunk_count": len(results),
            "chunk_ids": [c.chunk_id for c, _ in results],
        }
        status = RetrievalStatus(
            state="ok" if results else "empty",
            chunk_count=len(results),
            message=(
                f"本地知识库返回 {len(results)} 个片段（{mode} 模式，{self.method} 检索）。"
                if results
                else "本地知识库未召回片段，未使用知识库资料。"
            ),
        )
        return RetrievalResult(
            chunks=[
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
                    "scope": chunk.scope,
                },
            )
            for chunk, score in results
            ],
            status=status,
        )
