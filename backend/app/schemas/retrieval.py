from pydantic import Field, field_validator

from app.schemas.base import SchemaModel


class KnowledgeQuery(SchemaModel):
    query: str = Field(min_length=1, max_length=1000)
    purpose: str = Field(min_length=1, max_length=500)

    @field_validator("query", "purpose")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("查询和用途说明不能是空白文本。")
        return value


class KnowledgeQueryPlan(SchemaModel):
    queries: list[KnowledgeQuery] = Field(min_length=1, max_length=4)
