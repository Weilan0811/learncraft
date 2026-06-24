import json

from pydantic import BaseModel, ValidationError


def build_schema_instruction(schema: type[BaseModel]) -> str:
    return json.dumps(schema.model_json_schema(), ensure_ascii=False)


def format_parse_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return json.dumps(exc.errors(), ensure_ascii=False)
    return f"{type(exc).__name__}: {exc}"
