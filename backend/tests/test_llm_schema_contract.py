import json

from pydantic import BaseModel, ValidationError, model_validator

from app.services.llm.schema_contract import format_parse_error


class RejectsCustomValidator(BaseModel):
    value: int

    @model_validator(mode="after")
    def reject_value(self) -> "RejectsCustomValidator":
        raise ValueError("rejected by custom validator")


def test_format_parse_error_serializes_custom_validator_context() -> None:
    try:
        RejectsCustomValidator(value=1)
    except ValidationError as exc:
        message = format_parse_error(exc)
    else:
        raise AssertionError("expected ValidationError")

    payload = json.loads(message)
    assert isinstance(payload, list)
    assert "rejected by custom validator" in message


def test_format_parse_error_handles_regular_exceptions() -> None:
    message = format_parse_error(ValueError("plain failure"))
    assert message == "ValueError: plain failure"
