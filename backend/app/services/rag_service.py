from pathlib import Path
from typing import Callable, Protocol

import httpx

from app.core.config import Settings, get_settings
from app.schemas.request import ContentGenerationRequest
from app.schemas.state import RetrievedChunk


class EmbeddingService(Protocol):
    def embed_query(self, text: str) -> list[float]:
        """Return an embedding vector for a search query."""
        ...


class RAGService(Protocol):
    def retrieve(self, request: ContentGenerationRequest, stage: str, section_hint: str | None = None) -> list[RetrievedChunk]:
        """Retrieve knowledge chunks for the current generation stage."""
        ...


class StubRAGService:
    def retrieve(self, request: ContentGenerationRequest, stage: str, section_hint: str | None = None) -> list[RetrievedChunk]:
        # TODO(MVP-retriever): Replace with keyword/vector retrieval over at
        # least one knowledge base, including dedupe, ranking, max token limits,
        # source metadata, and section-level secondary retrieval.
        return [
            RetrievedChunk(
                id="chunk_stub",
                source_id=request.knowledge_base_ids[0] if request.knowledge_base_ids else "kb_stub",
                source_title="Stub Knowledge Source",
                content=f"{request.topic} 的知识库占位片段，用于支撑后续 Planner 与 Generator。",
                score=1.0,
                metadata={"stage": stage, "section_hint": section_hint or ""},
            )
        ]


class BailianEmbeddingService:
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-v3",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout_seconds: float = 60.0,
        client: object | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("Bailian API key is required for real embedding calls.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.client = client or httpx.Client(timeout=timeout_seconds)

    def embed_query(self, text: str) -> list[float]:
        response = self.client.post(
            f"{self.base_url}/embeddings",
            json={"model": self.model, "input": text},
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("data", []) if isinstance(data, dict) else []
        if not embeddings or not isinstance(embeddings[0], dict):
            raise RuntimeError("Bailian embedding response did not include data.")
        embedding = embeddings[0].get("embedding")
        if not isinstance(embedding, list):
            raise RuntimeError("Bailian embedding response did not include an embedding vector.")
        return [float(value) for value in embedding]


class QdrantRAGService:
    def __init__(
        self,
        qdrant_path: str | Path = "storage/qdrant_data",
        default_collection: str = "default",
        embedding_service: EmbeddingService | None = None,
        top_k: int = 5,
        max_chars: int = 6000,
        vector_store_factory: Callable[[str], object] | None = None,
    ) -> None:
        self.qdrant_path = Path(qdrant_path)
        self.default_collection = default_collection
        self.embedding_service = embedding_service
        self.top_k = top_k
        self.max_chars = max_chars
        self.vector_store_factory = vector_store_factory

    def retrieve(self, request: ContentGenerationRequest, stage: str, section_hint: str | None = None) -> list[RetrievedChunk]:
        collection = request.knowledge_base_ids[0] if request.knowledge_base_ids else self.default_collection
        try:
            vector_store = self._get_vector_store(collection)
            raw_results = vector_store.similarity_search_with_score(
                self._build_query(request=request, stage=stage, section_hint=section_hint),
                k=self.top_k,
            )
        except Exception:
            return []
        return self._map_results(raw_results, collection=collection, stage=stage, section_hint=section_hint)

    def _get_vector_store(self, collection: str) -> object:
        if self.vector_store_factory is not None:
            return self.vector_store_factory(collection)
        if self.embedding_service is None:
            raise RuntimeError("Embedding service is required for Qdrant retrieval.")
        if not self.qdrant_path.exists():
            raise RuntimeError(f"Qdrant path does not exist: {self.qdrant_path}")
        try:
            from langchain_qdrant import QdrantVectorStore
        except ImportError as exc:
            raise RuntimeError("langchain_qdrant is not installed.") from exc
        return QdrantVectorStore.from_existing_collection(
            embedding=self.embedding_service,
            collection_name=collection,
            path=str(self.qdrant_path),
        )

    @staticmethod
    def _build_query(request: ContentGenerationRequest, stage: str, section_hint: str | None) -> str:
        parts = [request.topic, request.user_prompt, stage]
        if request.system_prompt:
            parts.append(request.system_prompt)
        if section_hint:
            parts.append(section_hint)
        return "\n".join(parts)

    def _map_results(
        self,
        raw_results: list[tuple[object, float]],
        collection: str,
        stage: str,
        section_hint: str | None,
    ) -> list[RetrievedChunk]:
        chunks: list[RetrievedChunk] = []
        seen: set[str] = set()
        total_chars = 0
        deduped_results: list[tuple[object, float]] = []
        for document, score in raw_results:
            content = getattr(document, "page_content", "")
            metadata = dict(getattr(document, "metadata", {}) or {})
            dedupe_key = metadata.get("id") or metadata.get("chunk_id") or content
            if str(dedupe_key) in seen or content in seen:
                continue
            seen.add(str(dedupe_key))
            seen.add(content)
            deduped_results.append((document, score))

        seen.clear()
        for document, score in sorted(deduped_results, key=lambda item: item[1], reverse=True):
            content = getattr(document, "page_content", "")
            metadata = dict(getattr(document, "metadata", {}) or {})
            if not isinstance(content, str) or not content:
                continue
            if total_chars >= self.max_chars:
                break
            total_chars += len(content)
            chunk_id = str(metadata.get("id") or metadata.get("chunk_id") or f"chunk_{len(chunks) + 1}")
            source_id = str(metadata.get("source_id") or metadata.get("document_id") or collection)
            source_title = str(metadata.get("source_title") or metadata.get("title") or source_id)
            metadata.update({"collection": collection, "stage": stage, "section_hint": section_hint or ""})
            chunks.append(
                RetrievedChunk(
                    id=chunk_id,
                    source_id=source_id,
                    source_title=source_title,
                    content=content,
                    score=float(score),
                    metadata=metadata,
                )
            )
        return chunks


def get_rag_service(settings: Settings | None = None) -> RAGService:
    settings = settings or get_settings()
    if settings.provider_mode == "stub":
        return StubRAGService()
    if settings.embedding_provider != "bailian":
        raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
    embedding_service = BailianEmbeddingService(
        api_key=settings.bailian_api_key or "",
        model=settings.embedding_model,
        base_url=settings.bailian_base_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    return QdrantRAGService(
        qdrant_path=settings.qdrant_path,
        default_collection=settings.qdrant_collection,
        embedding_service=embedding_service,
        top_k=settings.retrieval_top_k,
        max_chars=settings.max_retrieval_chars,
    )
