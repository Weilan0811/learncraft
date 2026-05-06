from typing import Protocol

from app.schemas.request import ContentGenerationRequest
from app.schemas.state import RetrievedChunk


class RAGService(Protocol):
    def retrieve(self, request: ContentGenerationRequest, stage: str, section_hint: str | None = None) -> list[RetrievedChunk]:
        """Retrieve knowledge chunks for the current generation stage."""
        ...


class StubRAGService:
    def retrieve(self, request: ContentGenerationRequest, stage: str, section_hint: str | None = None) -> list[RetrievedChunk]:
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
