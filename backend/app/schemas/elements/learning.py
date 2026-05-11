from typing import Literal

from pydantic import Field

from app.schemas.elements.common import BaseElement


class TextElement(BaseElement):
    type: Literal["text"] = "text"
    content: str
    citations: list[str] = Field(default_factory=list)


class TableElement(BaseElement):
    type: Literal["table"] = "table"
    columns: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)


class QuizElement(BaseElement):
    type: Literal["quiz"] = "quiz"
    questions: list[dict[str, object]] = Field(default_factory=list)
    # TODO(P1-quiz): Replace dict questions with typed single-choice,
    # multi-choice, and short-answer schemas.


class Citation(BaseElement):
    type: Literal["citation"] = "citation"
    source_id: str
    source_title: str
    content: str
    url: str | None = None
