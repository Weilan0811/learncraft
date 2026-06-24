import base64
from pathlib import Path
from uuid import uuid4

import httpx
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
    monkeypatch.setenv("CONTENT_GENERATOR_KB_RETRIEVAL_TOP_K", "3")
    monkeypatch.setenv("CONTENT_GENERATOR_KB_API_BASE_URL", "")
    monkeypatch.delenv("CONTENT_GENERATOR_TEXT_PROVIDER", raising=False)
    monkeypatch.delenv("KB_API_BASE_URL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.provider_mode == "stub"
    assert settings.text_provider == "bailian"
    assert settings.text_model == "custom-chat"
    assert settings.image_provider == "apimart"
    assert settings.image_model == "gpt-image-2"
    assert settings.image_resolution == "1k"
    assert settings.apimart_api_key == "apimart-test"
    assert settings.apimart_base_url == "https://api.apimart.ai/v1"
    assert settings.bailian_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert settings.kb_api_base_url == ""
    assert settings.kb_retrieval_top_k == 3


def test_llm_service_parses_mocked_structured_json() -> None:
    from app.core.telemetry import drain_provider_metrics
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
    metrics = drain_provider_metrics(task_id="task_llm", node="plan_outline")
    assert metrics[0].provider == "Bailian"
    assert metrics[0].model == "qwen3.5-flash"
    assert metrics[0].total_tokens == 42


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


def test_openai_compatible_llm_service_tracks_retry_count() -> None:
    from app.services.llm import OpenAICompatibleLLMService

    class FakeClient:
        def __init__(self) -> None:
            self.calls = 0

        def post(self, url: str, **kwargs: object) -> FakeResponse:
            self.calls += 1
            if self.calls == 1:
                raise httpx.ConnectError("temporary outage")
            return FakeResponse(
                {"choices": [{"message": {"content": '{"title": "重试后", "points": ["成功"]}'}}]}
            )

    client = FakeClient()
    service = OpenAICompatibleLLMService(
        provider_name="bailian",
        api_key="sk-test",
        model="qwen3.5-flash",
        base_url="https://example.test/v1",
        client=client,
        max_retries=1,
        sleep=lambda _seconds: None,
    )

    result = service.generate_structured("生成大纲", DemoSchema)

    assert result.title == "重试后"
    assert client.calls == 2
    assert service.last_retry_count == 1


def test_deepseek_service_uses_openai_compatible_base_class() -> None:
    from app.services.llm import DeepseekLLMService, OpenAICompatibleLLMService

    service = DeepseekLLMService(api_key="sk-test", model="deepseek-chat", client=object())

    assert isinstance(service, OpenAICompatibleLLMService)


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

    assert "low-density teaching illustration" in prompt
    assert "medium-sized right-side panel" in prompt
    assert "No infographic" in prompt


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


def test_external_kb_service_maps_api_response_to_chunks() -> None:
    from app.services.rag_service import ExternalKBService

    class FakeClient:
        def post(self, url: str, **kwargs: object) -> FakeResponse:
            assert url.endswith("/v1/knowledge/retrieve")
            body = kwargs["json"]
            assert body["top_k"] == 3
            assert "planning" in body["query"]
            return FakeResponse(
                {
                    "ok": True,
                    "items": [
                        {"path": "overview.md", "title": "Overview", "text": "AI Agent overview content"},
                        {"path": "sources/agent.md", "title": "Agent Deep Dive", "text": "Detailed agent content"},
                    ],
                }
            )

    service = ExternalKBService(
        base_url="https://kb.example.test",
        api_key="test-key",
        top_k=3,
        max_chars_per_item=8000,
        client=FakeClient(),
    )
    request = ContentGenerationRequest(
        content_type="lecture",
        topic="人工智能",
        user_prompt="生成讲义",
        knowledge_base_ids=["kb_ai"],
    )

    chunks = service.retrieve(request, stage="planning")

    assert len(chunks) == 2
    assert chunks[0].id == "overview.md"
    assert chunks[0].source_title == "Overview"
    assert chunks[0].content == "AI Agent overview content"
    assert chunks[0].metadata["stage"] == "planning"
    assert chunks[1].source_id == "sources/agent.md"


def test_external_kb_service_returns_empty_on_failure() -> None:
    from app.services.rag_service import ExternalKBService

    class FakeClient:
        def post(self, url: str, **kwargs: object) -> FakeResponse:
            raise httpx.ConnectError("unreachable")

    service = ExternalKBService(
        base_url="https://kb.example.test",
        client=FakeClient(),
    )
    request = ContentGenerationRequest(content_type="lecture", topic="人工智能", user_prompt="生成讲义")

    assert service.retrieve(request, stage="planning") == []


def test_external_kb_service_returns_empty_when_api_reports_not_ok() -> None:
    from app.services.rag_service import ExternalKBService

    class FakeClient:
        def post(self, url: str, **kwargs: object) -> FakeResponse:
            return FakeResponse({"ok": False, "error": "internal error"})

    service = ExternalKBService(
        base_url="https://kb.example.test",
        client=FakeClient(),
    )
    request = ContentGenerationRequest(content_type="lecture", topic="人工智能", user_prompt="生成讲义")

    assert service.retrieve(request, stage="planning") == []
