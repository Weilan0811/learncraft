from app.schemas.learning import CreateSessionRequest, LearningEventPayload, SubmitEventRequest
from app.services.learning_service import InMemoryLearningService


def test_learning_service_counts_scenario_discussion_as_answered() -> None:
    service = InMemoryLearningService()
    session = service.create_session("lesson_1", CreateSessionRequest())

    service.submit_event(
        "lesson_1",
        session.session_id,
        SubmitEventRequest(
            section_id="unit_1",
            block_id="unit_1_sd",
            interaction_id="i_sd",
            event_type="scenario_discussion_submitted",
            payload=LearningEventPayload(
                answer_text="我会让讲解由 LLM 生成，互动由模板生成。",
                reference_points=["讲解由 LLM 生成", "互动由模板生成"],
                matched_points=["讲解由 LLM 生成"],
                heuristic_score=50,
            ),
        ),
    )

    state = service.get_session_state("lesson_1", session.session_id)

    assert state.total_events == 1
    assert state.interaction_summary["total_answered"] == 1
