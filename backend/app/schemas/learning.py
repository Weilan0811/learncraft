"""
P0 Learning Session and LearningEvent schemas.
"""

from typing import Literal
from pydantic import Field
from app.schemas.base import SchemaModel


# ---------------------------------------------------------------------------
# LearningEvent payload
# ---------------------------------------------------------------------------

class LearningEventPayload(SchemaModel):
    selected_option_ids: list[str] = Field(default_factory=list)
    correct_option_ids: list[str] = Field(default_factory=list)
    ordered_item_ids: list[str] = Field(default_factory=list)
    match_pairs: dict[str, str] = Field(default_factory=dict)
    answer_text: str | None = None
    is_correct: bool | None = None
    reference_points: list[str] = Field(default_factory=list)
    matched_points: list[str] = Field(default_factory=list)
    heuristic_score: int | None = None
    client_timestamp: str | None = None
    confidence: Literal["low", "medium", "high"] | None = None
    time_spent_seconds: int | None = None


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CreateSessionRequest(SchemaModel):
    """No extra fields needed for P0 — session is created from the lesson."""


class SubmitEventRequest(SchemaModel):
    section_id: str
    block_id: str | None = None
    interaction_id: str | None = None
    event_type: Literal[
        "single_choice_answered",
        "multiple_choice_answered",
        "short_answer_submitted",
        "scenario_discussion_submitted",
        "drag_match_submitted",
        "sequence_submitted",
        "socratic_round_answered",
        "scenario_choice_selected",
        "hint_requested",
        "confused_clicked",
    ]
    payload: LearningEventPayload = Field(default_factory=LearningEventPayload)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class SessionResponse(SchemaModel):
    session_id: str
    lesson_id: str
    state: dict = Field(default_factory=dict)


class EventFeedback(SchemaModel):
    message: str = "Your answer has been recorded."
    tone: Literal["encouraging", "corrective", "socratic"] = "encouraging"


class EventResponse(SchemaModel):
    event_id: str
    feedback: EventFeedback = Field(default_factory=EventFeedback)
    event_saved: bool = True


class SessionStateResponse(SchemaModel):
    session_id: str
    lesson_id: str
    total_events: int = 0
    interaction_summary: dict = Field(default_factory=dict)
