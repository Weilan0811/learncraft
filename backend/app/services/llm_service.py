from typing import Protocol, TypeVar

from pydantic import BaseModel


StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


class LLMService(Protocol):
    def generate_structured(self, prompt: str, schema: type[StructuredModel]) -> StructuredModel:
        """Generate a schema-validated response from an LLM.

        TODO: Connect to the configured model provider with retries and tracing.
        """
        ...


class StubLLMService:
    def generate_structured(self, prompt: str, schema: type[StructuredModel]) -> StructuredModel:
        raise NotImplementedError("LLM generation is intentionally stubbed in the skeleton.")
