from dataclasses import dataclass, field
from typing import Protocol

from app.core.config import Settings, get_settings
from app.schemas.request import ContentGenerationRequest
from app.schemas.state import RetrievalStatus, RetrievedChunk


@dataclass(frozen=True)
class RetrievalResult:
    chunks: list[RetrievedChunk]
    status: RetrievalStatus
    queries: list[str] = field(default_factory=list)
    query_results: list[dict[str, object]] = field(default_factory=list)


class RAGService(Protocol):
    def retrieve(
        self,
        request: ContentGenerationRequest,
        stage: str,
        section_hint: str | None = None,
        queries: list[str] | None = None,
    ) -> RetrievalResult:
        """Retrieve knowledge chunks and report why the result is empty."""
        ...


class DisabledRAGService:
    """Retrieval stays off until the standalone knowledge base module is wired in."""

    def retrieve(
        self,
        request: ContentGenerationRequest,
        stage: str,
        section_hint: str | None = None,
        queries: list[str] | None = None,
    ) -> RetrievalResult:
        return RetrievalResult(chunks=[], status=RetrievalStatus())


def get_rag_service(settings: Settings | None = None) -> RAGService:
    settings = settings or get_settings()
    if settings.kb_provider == "local":
        from app.services.local_kb_service import LocalKBService

        return LocalKBService(top_k=settings.kb_retrieval_top_k, api_key=settings.bailian_api_key or "")
    # No external KB API exists anymore; anything other than "local" keeps retrieval off.
    return DisabledRAGService()
