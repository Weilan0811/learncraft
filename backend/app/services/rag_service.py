from __future__ import annotations

import httpx

from app.core.config import Settings, get_settings
from app.schemas.request import ContentGenerationRequest
from app.schemas.state import RetrievedChunk


class RAGService:
    def retrieve(self, request: ContentGenerationRequest, stage: str, section_hint: str | None = None) -> list[RetrievedChunk]:
        """Retrieve knowledge chunks for the current generation stage."""
        ...


class StubRAGService(RAGService):
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


class ExternalKBService(RAGService):
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        top_k: int = 5,
        max_chars_per_item: int = 8000,
        timeout_seconds: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        if not base_url:
            raise ValueError("External KB API base URL is required for real retrieval.")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.top_k = top_k
        self.max_chars_per_item = max_chars_per_item
        self.timeout_seconds = timeout_seconds
        self.client = client or httpx.Client(timeout=timeout_seconds)
        self.last_diagnostics: dict[str, object] = {}

    def retrieve(self, request: ContentGenerationRequest, stage: str, section_hint: str | None = None) -> list[RetrievedChunk]:
        query = self._build_query(request=request, stage=stage, section_hint=section_hint)
        self.last_diagnostics = {
            "stage": stage,
            "query_preview": query[:500],
            "top_k": self.top_k,
            "base_url": self.base_url,
        }
        try:
            response = self.client.post(
                f"{self.base_url}/v1/knowledge/retrieve",
                json={
                    "query": query,
                    "top_k": self.top_k,
                    "include": ["title", "text"],
                    "max_chars_per_item": self.max_chars_per_item,
                },
                headers=self._build_headers(),
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            self.last_diagnostics.update({"http_status": getattr(response, "status_code", None)})
        except Exception as exc:
            self.last_diagnostics.update(
                {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )
            return []
        if not isinstance(data, dict) or not data.get("ok"):
            self.last_diagnostics.update(
                {
                    "status": "invalid_response",
                    "ok": data.get("ok") if isinstance(data, dict) else None,
                    "response_type": type(data).__name__,
                }
            )
            return []
        items = data.get("items") or []
        chunks = self._map_items(items, stage=stage, section_hint=section_hint)
        self.last_diagnostics.update(
            {
                "status": "ok",
                "ok": True,
                "item_count": len(items) if isinstance(items, list) else 0,
                "chunk_count": len(chunks),
                "chunk_ids": [chunk.id for chunk in chunks],
            }
        )
        return chunks

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @staticmethod
    def _build_query(request: ContentGenerationRequest, stage: str, section_hint: str | None) -> str:
        parts = [request.topic, request.user_prompt, stage]
        if request.system_prompt:
            parts.append(request.system_prompt)
        if section_hint:
            parts.append(section_hint)
        return "\n".join(parts)

    @staticmethod
    def _map_items(items: list[dict[str, object]], stage: str, section_hint: str | None) -> list[RetrievedChunk]:
        chunks: list[RetrievedChunk] = []
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            path = str(item.get("path") or f"item_{index + 1}")
            title = str(item.get("title") or path)
            text = str(item.get("text") or "")
            if not text:
                continue
            chunks.append(
                RetrievedChunk(
                    id=path,
                    source_id=path,
                    source_title=title,
                    content=text,
                    score=1.0,
                    metadata={"stage": stage, "section_hint": section_hint or ""},
                )
            )
        return chunks


def get_rag_service(settings: Settings | None = None) -> RAGService:
    settings = settings or get_settings()
    if settings.provider_mode == "stub":
        return StubRAGService()
    if settings.kb_provider == "local":
        from app.services.local_kb_service import LocalKBService

        return LocalKBService(top_k=settings.kb_retrieval_top_k, api_key=settings.bailian_api_key or "")
    return ExternalKBService(
        base_url=settings.kb_api_base_url,
        api_key=settings.kb_api_key,
        top_k=settings.kb_retrieval_top_k,
        max_chars_per_item=settings.kb_max_chars_per_item,
        timeout_seconds=settings.kb_request_timeout_seconds,
    )
