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


def test_learning_service_lists_events_for_offline_handout() -> None:
    service = InMemoryLearningService()
    session = service.create_session("lesson_1", CreateSessionRequest())

    service.submit_event(
        "lesson_1",
        session.session_id,
        SubmitEventRequest(
            section_id="unit_1",
            block_id="unit_1_q1",
            interaction_id="i_q1",
            event_type="single_choice_answered",
            payload=LearningEventPayload(selected_option_ids=["a"], correct_option_ids=["a"], is_correct=True),
        ),
    )

    events = service.list_events("lesson_1", session.session_id)

    assert len(events) == 1
    assert events[0]["interaction_id"] == "i_q1"
    assert events[0]["payload"]["selected_option_ids"] == ["a"]
