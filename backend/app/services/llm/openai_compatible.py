import json
import time
from collections.abc import Callable

import httpx
from pydantic import BaseModel, ValidationError

from app.services.llm.base import LLMGenerationError, StructuredModel
from app.services.llm.schema_contract import build_schema_instruction, format_parse_error


class StubLLMService:
    last_usage: dict[str, object] = {}
    last_retry_count: int = 0

    def chat(self, user_message: str, system_prompt: str = "") -> str:
        raise NotImplementedError("LLM generation is intentionally stubbed in the skeleton.")

    def generate_structured(self, prompt: str, schema: type[StructuredModel]) -> StructuredModel:
        raise NotImplementedError("LLM generation is intentionally stubbed in the skeleton.")


class OpenAICompatibleLLMService:
    def __init__(
        self,
        *,
        provider_name: str,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        client: object | None = None,
        include_json_response_format: bool = False,
        repair_prompt_language: str = "zh",
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key:
            raise ValueError(f"{provider_name} API key is required for real LLM calls.")
        self.provider_name = provider_name
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.client = client or httpx.Client(timeout=timeout_seconds)
        self.include_json_response_format = include_json_response_format
        self.repair_prompt_language = repair_prompt_language
        self.sleep = sleep
        self.last_usage: dict[str, object] = {}
        self.last_retry_count: int = 0

    def chat(self, user_message: str, system_prompt: str = "") -> str:
        payload: dict[str, object] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
        }
        if self.include_json_response_format:
            payload["response_format"] = {"type": "json_object"}
        return self._extract_content(self._post_with_retries(f"{self.base_url}/chat/completions", payload, self._headers()))

    def generate_structured(self, prompt: str, schema: type[StructuredModel]) -> StructuredModel:
        content = self._chat_with_schema(prompt=prompt, schema=schema)
        try:
            return self._parse_content(content, schema)
        except (json.JSONDecodeError, ValidationError, TypeError):
            return self._repair_and_parse(content, schema)

    def _repair_and_parse(self, content: str, schema: type[StructuredModel]) -> StructuredModel:
        if self.repair_prompt_language == "en":
            repair_prompt = (
                "Please fix the content below to be strict JSON that must conform to the given JSON Schema. "
                "Do not output Markdown, do not output explanations, only output JSON.\n\n"
                f"JSON Schema:\n{build_schema_instruction(schema)}\n\n"
                f"Original content:\n{content}"
            )
        else:
            repair_prompt = (
                "请把下面内容修复为严格 JSON，且必须符合给定 JSON Schema。"
                "不要输出 Markdown，不要输出解释，只输出 JSON。\n\n"
                f"JSON Schema:\n{build_schema_instruction(schema)}\n\n"
                f"原始内容:\n{content}"
            )
        repaired = self._chat_with_schema(prompt=repair_prompt, schema=schema)
        try:
            return self._parse_content(repaired, schema)
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise LLMGenerationError(
                f"LLM response failed schema validation after repair for {schema.__name__}: {format_parse_error(exc)}"
            ) from exc

    def _chat_with_schema(self, prompt: str, schema: type[BaseModel]) -> str:
        payload: dict[str, object] = {
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
                        f"{build_schema_instruction(schema)}"
                    ),
                },
            ],
        }
        if self.include_json_response_format:
            payload["response_format"] = {"type": "json_object"}
        return self._extract_content(self._post_with_retries(f"{self.base_url}/chat/completions", payload, self._headers()))

    def _post_with_retries(self, url: str, payload: dict[str, object], headers: dict[str, str]) -> object:
        last_error: Exception | None = None
        self.last_retry_count = 0
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.post(url, json=payload, headers=headers, timeout=self.timeout_seconds)
                response.raise_for_status()
                return response
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                self.last_retry_count += 1
                self.sleep(min(2**attempt, 5))
        detail = f"{type(last_error).__name__}: {last_error}" if last_error else "unknown error"
        raise LLMGenerationError(f"LLM request failed after retries: {detail}") from last_error

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


class BailianLLMService(OpenAICompatibleLLMService):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        client: object | None = None,
    ) -> None:
        super().__init__(
            provider_name="Bailian",
            api_key=api_key,
            model=model,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            client=client,
            include_json_response_format=True,
            repair_prompt_language="zh",
        )


class DeepseekLLMService(OpenAICompatibleLLMService):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.deepseek.com",
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        client: object | None = None,
    ) -> None:
        super().__init__(
            provider_name="Deepseek",
            api_key=api_key,
            model=model,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            client=client,
            include_json_response_format=False,
            repair_prompt_language="en",
        )
