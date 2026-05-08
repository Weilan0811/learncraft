from app.schemas.outline import Outline, OutlineSection, OutlineUnit, RecommendedElement
from app.schemas.state import ContentGenerationState
from app.workflows.nodes.helpers import build_progress


def plan_outline(state: ContentGenerationState) -> dict[str, object]:
    chunk_ids = [chunk.id for chunk in state.planning_chunks]
    unit_type = "slide" if state.content_type == "slide_deck" else "section"
    element_recommendations = [
        RecommendedElement(type="image", purpose="展示核心概念或应用场景", priority="high"),
        RecommendedElement(type="mindmap", purpose="梳理知识结构", priority="medium"),
    ]
    unit = OutlineUnit(
        id="unit_001",
        order=1,
        unit_type=unit_type,
        title=state.topic,
        goal=f"建立对 {state.topic} 的基础理解",
        core_message=f"{state.topic} 的核心概念、结构和应用需要被清晰呈现。",
        key_points=["核心概念", "知识结构", "应用场景"],
        visual_strategy="title-content-visual",
        recommended_elements=element_recommendations,
        retrieval_queries=[state.topic, f"{state.topic} 核心概念"],
        source_chunk_ids=chunk_ids,
    )
    section = OutlineSection(
        id="sec_001",
        title=unit.title,
        goal=unit.goal,
        key_points=unit.key_points,
        recommended_elements=["image", "mindmap"],
        estimated_minutes=10,
        citations=chunk_ids,
    )
    outline = Outline(
        id=f"outline_{state.request_id}",
        content_type=state.content_type,
        title=state.topic,
        audience="待实现的目标受众",
        learning_objectives=[f"理解 {state.topic} 的核心概念"],
        units=[unit],
        sections=[section],
        metadata={"created_by": "planner_node", "stub": True},
    )
    return {
        "outline": outline,
        "current_node": "plan_outline",
        "progress": build_progress(stage="planning", current_node="plan_outline"),
    }


__all__ = ["plan_outline"]
