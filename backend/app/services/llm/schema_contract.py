import json

from pydantic import BaseModel, ValidationError


def build_schema_instruction(schema: type[BaseModel]) -> str:
    return json.dumps(schema.model_json_schema(), ensure_ascii=False)


def format_parse_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        try:
            errors = exc.errors(include_url=False, include_context=False, include_input=False)
        except TypeError:
            errors = exc.errors()
        return json.dumps(_json_safe(errors), ensure_ascii=False)
    return f"{type(exc).__name__}: {exc}"


def _json_safe(value: object) -> object:
    """Convert validation payloads into JSON-serializable values.

    Pydantic's ValidationError.errors() keeps the original exception object in
    ``ctx.error`` for custom validators. Serializing that payload directly used
    to raise "Object of type ValueError is not JSON serializable", hiding the
    real validation message and failing an entire slide unit.
    """
    if isinstance(value, BaseException):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
