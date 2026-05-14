import json
import time
from typing import Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings


StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


class LLMGenerationError(RuntimeError):
    """Raised when an LLM response cannot be converted into the requested schema."""


class LLMService(Protocol):
    def generate_structured(self, prompt: str, schema: type[StructuredModel]) -> StructuredModel:
        """Generate a schema-validated response from an LLM."""
        ...


class StubLLMService:
    def generate_structured(self, prompt: str, schema: type[StructuredModel]) -> StructuredModel:
        raise NotImplementedError("LLM generation is intentionally stubbed in the skeleton.")


class BailianLLMService:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        client: object | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("Bailian API key is required for real LLM calls.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.client = client or httpx.Client(timeout=timeout_seconds)
        self.last_usage: dict[str, object] = {}

    def chat(self, user_message: str, system_prompt: str = "") -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
            "response_format": {"type": "json_object"},
        }
        return self._extract_content(self._post_with_retries(f"{self.base_url}/chat/completions", payload, self._headers()))

    def generate_structured(self, prompt: str, schema: type[StructuredModel]) -> StructuredModel:
        content = self._chat_with_schema(prompt=prompt, schema=schema)
        try:
            return self._parse_content(content, schema)
        except (json.JSONDecodeError, ValidationError, TypeError):
            return self._repair_and_parse(content, schema)

    def _repair_and_parse(self, content: str, schema: type[StructuredModel]) -> StructuredModel:
        repair_prompt = (
            "请把下面内容修复为严格 JSON，且必须符合给定 JSON Schema。"
            "不要输出 Markdown，不要输出解释，只输出 JSON。\n\n"
            f"JSON Schema:\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}\n\n"
            f"原始内容:\n{content}"
        )
        repaired = self._chat_with_schema(prompt=repair_prompt, schema=schema)
        try:
            return self._parse_content(repaired, schema)
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise LLMGenerationError("LLM response failed schema validation after repair.") from exc

    def _chat_with_schema(self, prompt: str, schema: type[BaseModel]) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You generate strictly valid JSON for backend services. "
                        "Return JSON only, with no Markdown fences or commentary."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"{prompt}\n\n"
                        "The response must validate against this JSON Schema:\n"
                        f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
        }
        return self._extract_content(self._post_with_retries(f"{self.base_url}/chat/completions", payload, self._headers()))

    def _post_with_retries(self, url: str, payload: dict[str, object], headers: dict[str, str]) -> object:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.post(url, json=payload, headers=headers, timeout=self.timeout_seconds)
                response.raise_for_status()
                return response
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(min(2**attempt, 5))
        raise LLMGenerationError("LLM request failed after retries.") from last_error

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _extract_content(self, response: object) -> str:
        data = response.json()
        self.last_usage = data.get("usage", {}) if isinstance(data, dict) else {}
        choices = data.get("choices", []) if isinstance(data, dict) else []
        if not choices:
            raise LLMGenerationError("LLM response did not include choices.")
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = message.get("content")
        if not isinstance(content, str):
            raise LLMGenerationError("LLM response did not include message content.")
        return content

    @staticmethod
    def _parse_content(content: str, schema: type[StructuredModel]) -> StructuredModel:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        return schema.model_validate(json.loads(cleaned))


def get_llm_service(settings: Settings | None = None) -> LLMService:
    settings = settings or get_settings()
    if settings.provider_mode == "stub":
        return StubLLMService()
    if settings.text_provider != "bailian":
        raise ValueError(f"Unsupported text provider: {settings.text_provider}")
    return BailianLLMService(
        api_key=settings.bailian_api_key or "",
        model=settings.text_model,
        base_url=settings.bailian_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        max_retries=settings.max_retries,
    )
