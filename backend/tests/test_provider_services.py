import base64
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import BaseModel

from app.core.config import Settings
from app.schemas.request import ContentGenerationRequest


class FakeResponse:
    def __init__(
        self,
        payload: dict[str, object] | None = None,
        content: bytes = b"",
        content_type: str = "application/json",
    ) -> None:
        self._payload = payload or {}
        self.content = content
        self.headers = {"content-type": content_type}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


class DemoSchema(BaseModel):
    title: str
    points: list[str]


def provider_storage_root() -> Path:
    root = Path("storage") / "test_provider_services" / uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_settings_load_provider_defaults_and_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    monkeypatch.setenv("CONTENT_GENERATOR_APIMART_API_KEY", "apimart-test")
    monkeypatch.setenv("CONTENT_GENERATOR_TEXT_MODEL", "custom-chat")
    monkeypatch.setenv("CONTENT_GENERATOR_RETRIEVAL_TOP_K", "3")

    settings = Settings()

    assert settings.provider_mode == "stub"
    assert settings.text_provider == "bailian"
    assert settings.text_model == "custom-chat"
    assert settings.image_provider == "apimart"
    assert settings.image_model == "gpt-image-2"
    assert settings.image_resolution == "1k"
    assert settings.embedding_provider == "bailian"
    assert settings.embedding_model == "text-embedding-v3"
    assert settings.apimart_api_key == "apimart-test"
    assert settings.apimart_base_url == "https://api.apimart.ai/v1"
    assert settings.bailian_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert settings.qdrant_path == "storage/qdrant_data"
    assert settings.retrieval_top_k == 3


def test_llm_service_parses_mocked_structured_json() -> None:
    from app.services.llm_service import BailianLLMService

    class FakeClient:
        def post(self, url: str, **kwargs: object) -> FakeResponse:
            assert url.endswith("/chat/completions")
            return FakeResponse(
                {
                    "choices": [{"message": {"content": '{"title": "人工智能基础", "points": ["定义", "应用"]}'}}],
                    "usage": {"total_tokens": 42},
                }
            )

    service = BailianLLMService(api_key="sk-test", model="qwen3.5-flash", client=FakeClient())

    result = service.generate_structured("生成大纲", DemoSchema)

    assert result == DemoSchema(title="人工智能基础", points=["定义", "应用"])
    assert service.last_usage == {"total_tokens": 42}


def test_llm_service_repairs_invalid_structured_json_once() -> None:
    from app.services.llm_service import BailianLLMService

    class FakeClient:
        def __init__(self) -> None:
            self.calls = 0

        def post(self, url: str, **kwargs: object) -> FakeResponse:
            self.calls += 1
            content = "not json" if self.calls == 1 else '{"title": "修复后", "points": ["结构化"]}'
            return FakeResponse({"choices": [{"message": {"content": content}}]})

    client = FakeClient()
    service = BailianLLMService(api_key="sk-test", model="qwen3.5-flash", client=client, max_retries=0)

    result = service.generate_structured("生成大纲", DemoSchema)

    assert result.title == "修复后"
    assert client.calls == 2


def test_apimart_image_service_polls_downloads_and_persists_image() -> None:
    from app.services.image_generation_service import APIMartImageGenerationService
    from app.services.storage_service import LocalStorageService

    class FakeClient:
        def __init__(self) -> None:
            self.posts: list[dict[str, object]] = []

        def post(self, url: str, **kwargs: object) -> FakeResponse:
            self.posts.append(kwargs["json"])  # type: ignore[arg-type]
            assert url.endswith("/images/generations")
            return FakeResponse({"task_id": "task_123"})

        def get(self, url: str, **kwargs: object) -> FakeResponse:
            if url.endswith("/tasks/task_123"):
                return FakeResponse(
                    {
                        "data": {
                            "status": "completed",
                            "result": {"images": [{"url": ["https://example.test/image.png"]}]},
                        }
                    }
                )
            assert url == "https://example.test/image.png"
            return FakeResponse(content=b"\x89PNG\r\n\x1a\nfake", content_type="image/png")

    client = FakeClient()
    storage = LocalStorageService(storage_root=provider_storage_root(), public_base_url="/api/assets")
    service = APIMartImageGenerationService(
        api_key="apimart-test",
        model="gpt-image-2",
        resolution="1k",
        storage_service=storage,
        client=client,
        poll_interval_seconds=0,
    )

    image = service.generate_image("概念图", "展示 AI 在教育中的应用", "16:9")

    assert client.posts[0]["model"] == "gpt-image-2"
    assert client.posts[0]["resolution"] == "1k"
    assert image.asset_url.startswith("/api/assets/")
    assert image.asset_url.endswith("/download")
    assert image.metadata["provider"] == "apimart"
    assert image.metadata["task_id"] == "task_123"
    assert storage.read_bytes(image.id).startswith(b"\x89PNG")


def test_apimart_image_service_accepts_documented_submitted_task_response() -> None:
    from app.services.image_generation_service import APIMartImageGenerationService
    from app.services.storage_service import LocalStorageService

    class FakeClient:
        def post(self, url: str, **kwargs: object) -> FakeResponse:
            return FakeResponse({"code": 200, "data": [{"status": "submitted", "task_id": "task_doc"}]})

        def get(self, url: str, **kwargs: object) -> FakeResponse:
            if url.endswith("/tasks/task_doc"):
                return FakeResponse(
                    {
                        "code": 200,
                        "data": {
                            "status": "completed",
                            "result": {"images": [{"url": ["https://example.test/doc-shape.png"]}]},
                        },
                    }
                )
            assert url == "https://example.test/doc-shape.png"
            return FakeResponse(content=b"\x89PNG\r\n\x1a\ndoc", content_type="image/png")

    storage = LocalStorageService(storage_root=provider_storage_root(), public_base_url="/api/assets")
    service = APIMartImageGenerationService(
        api_key="apimart-test",
        model="gpt-image-2",
        storage_service=storage,
        client=FakeClient(),
        poll_interval_seconds=0,
    )

    image = service.generate_image("Concept diagram", "show the agent workflow", "16:9")

    assert image.metadata["task_id"] == "task_doc"
    assert image.metadata["response_mode"] == "task"
    assert storage.read_bytes(image.id).startswith(b"\x89PNG")


def test_apimart_image_service_accepts_openai_compatible_url_response() -> None:
    from app.services.image_generation_service import APIMartImageGenerationService
    from app.services.storage_service import LocalStorageService

    class FakeClient:
        def __init__(self) -> None:
            self.posts: list[dict[str, object]] = []

        def post(self, url: str, **kwargs: object) -> FakeResponse:
            self.posts.append(kwargs["json"])  # type: ignore[arg-type]
            return FakeResponse({"data": [{"url": "https://example.test/direct.png"}]})

        def get(self, url: str, **kwargs: object) -> FakeResponse:
            assert url == "https://example.test/direct.png"
            return FakeResponse(content=b"\x89PNG\r\n\x1a\ndirect", content_type="image/png")

    storage = LocalStorageService(storage_root=provider_storage_root(), public_base_url="/api/assets")
    service = APIMartImageGenerationService(
        api_key="apimart-test",
        storage_service=storage,
        client=FakeClient(),
        poll_interval_seconds=0,
    )

    image = service.generate_image("Concept diagram", "show the agent workflow", "16:9")

    assert image.metadata["provider"] == "apimart"
    assert image.metadata["response_mode"] == "url"
    assert storage.read_bytes(image.id).startswith(b"\x89PNG")


def test_apimart_image_service_accepts_openai_compatible_b64_response() -> None:
    from app.services.image_generation_service import APIMartImageGenerationService
    from app.services.storage_service import LocalStorageService

    png_bytes = b"\x89PNG\r\n\x1a\nb64"

    class FakeClient:
        def post(self, url: str, **kwargs: object) -> FakeResponse:
            return FakeResponse({"data": [{"b64_json": base64.b64encode(png_bytes).decode("ascii")}]})

    storage = LocalStorageService(storage_root=provider_storage_root(), public_base_url="/api/assets")
    service = APIMartImageGenerationService(
        api_key="apimart-test",
        storage_service=storage,
        client=FakeClient(),
        poll_interval_seconds=0,
    )

    image = service.generate_image("Concept diagram", "show the agent workflow", "1:1")

    assert image.metadata["response_mode"] == "b64_json"
    assert image.format == "png"
    assert storage.read_bytes(image.id) == png_bytes


def test_apimart_image_service_rejects_empty_prompt_before_paid_submit() -> None:
    from app.services.image_generation_service import APIMartImageGenerationError, APIMartImageGenerationService
    from app.services.storage_service import LocalStorageService

    class FakeClient:
        def __init__(self) -> None:
            self.submit_count = 0

        def post(self, url: str, **kwargs: object) -> FakeResponse:
            self.submit_count += 1
            return FakeResponse({"task_id": "should_not_submit"})

    client = FakeClient()
    service = APIMartImageGenerationService(
        api_key="apimart-test",
        storage_service=LocalStorageService(storage_root=provider_storage_root()),
        client=client,
        poll_interval_seconds=0,
    )

    with pytest.raises(APIMartImageGenerationError, match="Image prompt is empty"):
        service.generate_image("Concept diagram", "   ", "16:9")

    assert client.submit_count == 0


def test_apimart_image_prompt_forbids_full_slide_layouts() -> None:
    from app.services.image_generation_service import APIMartImageGenerationService

    prompt = APIMartImageGenerationService._build_prompt(
        description="A timeline showing AI progress from rules to autonomous agents.",
        aspect_ratio="16:9",
    )

    assert "standalone illustration or diagram asset" in prompt
    assert "not a presentation slide" in prompt
    assert "Do not create a slide title" in prompt


def test_apimart_image_service_failed_task_raises_without_retrying_paid_submit() -> None:
    from app.services.image_generation_service import APIMartImageGenerationError, APIMartImageGenerationService
    from app.services.storage_service import LocalStorageService

    class FakeClient:
        def __init__(self) -> None:
            self.submit_count = 0

        def post(self, url: str, **kwargs: object) -> FakeResponse:
            self.submit_count += 1
            return FakeResponse({"task_id": "task_failed"})

        def get(self, url: str, **kwargs: object) -> FakeResponse:
            return FakeResponse({"data": {"status": "failed", "error": {"message": "bad prompt"}}})

    client = FakeClient()
    service = APIMartImageGenerationService(
        api_key="apimart-test",
        storage_service=LocalStorageService(storage_root=provider_storage_root()),
        client=client,
        poll_interval_seconds=0,
    )

    with pytest.raises(APIMartImageGenerationError, match="bad prompt"):
        service.generate_image("概念图", "bad", "1:1")

    assert client.submit_count == 1


def test_image_service_factory_can_select_bailian_provider() -> None:
    from app.services.image_generation_service import BailianImageGenerationService, get_image_generation_service

    settings = Settings(provider_mode="real", image_provider="bailian", bailian_api_key="sk-test")

    service = get_image_generation_service(settings=settings)

    assert isinstance(service, BailianImageGenerationService)


def test_qdrant_rag_service_maps_dedupes_sorts_and_limits_chunks() -> None:
    from app.services.rag_service import QdrantRAGService

    class FakeDoc:
        def __init__(self, content: str, metadata: dict[str, object]) -> None:
            self.page_content = content
            self.metadata = metadata

    class FakeVectorStore:
        def similarity_search_with_score(self, query: str, k: int) -> list[tuple[FakeDoc, float]]:
            assert "planning" in query
            assert k == 5
            return [
                (FakeDoc("A" * 12, {"id": "chunk_a", "source_id": "doc_a", "source_title": "Doc A"}), 0.9),
                (FakeDoc("B" * 20, {"id": "chunk_b", "source_id": "doc_b", "source_title": "Doc B"}), 0.7),
                (FakeDoc("A" * 12, {"id": "chunk_a_dup", "source_id": "doc_a", "source_title": "Doc A"}), 0.95),
            ]

    service = QdrantRAGService(
        vector_store_factory=lambda collection_name: FakeVectorStore(),
        top_k=5,
        max_chars=25,
        default_collection="default",
    )
    request = ContentGenerationRequest(
        content_type="lecture",
        topic="人工智能",
        user_prompt="生成讲义",
        knowledge_base_ids=["kb_ai"],
    )

    chunks = service.retrieve(request, stage="planning")

    assert [chunk.id for chunk in chunks] == ["chunk_a", "chunk_b"]
    assert chunks[0].metadata["collection"] == "kb_ai"
    assert chunks[1].metadata["stage"] == "planning"


def test_qdrant_rag_service_returns_empty_when_collection_unavailable() -> None:
    from app.services.rag_service import QdrantRAGService

    def unavailable(collection_name: str) -> object:
        raise RuntimeError("missing")

    service = QdrantRAGService(vector_store_factory=unavailable)
    request = ContentGenerationRequest(content_type="lecture", topic="人工智能", user_prompt="生成讲义")

    assert service.retrieve(request, stage="planning") == []
