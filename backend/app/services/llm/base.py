from typing import Protocol, TypeVar

from pydantic import BaseModel


StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


class LLMGenerationError(RuntimeError):
    """Raised when an LLM response cannot be converted into the requested schema."""


class LLMService(Protocol):
    last_usage: dict[str, object]
    last_retry_count: int

    def chat(self, user_message: str, system_prompt: str = "") -> str:
        """Generate a plain chat response."""
        ...

    def generate_structured(self, prompt: str, schema: type[StructuredModel]) -> StructuredModel:
        """Generate a schema-validated response from an LLM."""
        ...
