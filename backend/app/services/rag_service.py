from dataclasses import dataclass
from typing import Protocol

from app.schemas.request import ContentGenerationRequest
from app.schemas.state import RetrievalStatus, RetrievedChunk


@dataclass(frozen=True)
class RetrievalResult:
    chunks: list[RetrievedChunk]
    status: RetrievalStatus


class RAGService(Protocol):
    def retrieve(
        self,
        request: ContentGenerationRequest,
        stage: str,
        section_hint: str | None = None,
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
    ) -> RetrievalResult:
        return RetrievalResult(chunks=[], status=RetrievalStatus())


def get_rag_service() -> RAGService:
    return DisabledRAGService()
