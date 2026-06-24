from app.schemas.outline import OutlineUnit
from app.schemas.specs import InteractiveHtmlSectionSpec
from app.schemas.state import ContentGenerationState


def build_interactive_html_unit_spec_fallback(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> InteractiveHtmlSectionSpec:
    """Stub fallback producing a valid teaching design spec (no HTML)."""
    from app.schemas.specs.interactive_html import (
        InteractiveHtmlInteractionOption,
        InteractiveHtmlInteractionSpec,
        InteractiveHtmlTeachingBlock,
    )

    section_id = unit.id
    title = unit.title
    goal = unit.goal
    core = unit.core_message or unit.goal
    points = (unit.key_points or ["核心概念", "关键关系", "实践应用"])[:4]
    interaction_id = f"{section_id}_check"
    first_point = points[0] if points else "核心概念"

    return InteractiveHtmlSectionSpec(
        section_id=section_id,
        title=title,
        learning_goal=goal,
        narrative_goal=f"理解{title}的核心要点并形成清晰判断",
        teaching_flow=[
            InteractiveHtmlTeachingBlock(
                block_id=f"{section_id}_intro",
                block_type="intro",
                title=title,
                teaching_role="set_context",
                content_goal=core,
                must_cover=[core],
            ),
            InteractiveHtmlTeachingBlock(
                block_id=f"{section_id}_concepts",
                block_type="concept_explanation",
                title="关键概念线索",
                teaching_role="explain_core",
                content_goal="讲解本节核心概念及其相互关系",
                must_cover=points[:3],
            ),
            InteractiveHtmlTeachingBlock(
                block_id=f"{section_id}_check_block",
                block_type="single_choice",
                title="关键学习点诊断",
                teaching_role="diagnose_understanding",
                content_goal="诊断学习者对核心概念的理解程度",
                must_cover=[first_point],
                interaction_id=interaction_id,
            ),
            InteractiveHtmlTeachingBlock(
                block_id=f"{section_id}_reflection",
                block_type="reflection",
                title="学习目标收束",
                teaching_role="prompt_reflection",
                content_goal=goal,
                must_cover=[goal],
            ),
        ],
        interaction_specs=[
            InteractiveHtmlInteractionSpec(
                interaction_id=interaction_id,
                block_id=f"{section_id}_check_block",
                type="single_choice",
                event_type="single_choice_answered",
                target_concepts=[first_point],
                prompt="下面哪一项最能概括本节的关键学习点？",
                options=[
                    InteractiveHtmlInteractionOption(
                        id="a",
                        text=first_point,
                        is_correct=True,
                        feedback="正确。这个选项对应本节需要建立的核心理解。",
                    ),
                    InteractiveHtmlInteractionOption(
                        id="b",
                        text="只记住页面样式",
                        is_correct=False,
                        feedback="页面样式有助于学习体验，但不是本节知识的核心判断。",
                    ),
                    InteractiveHtmlInteractionOption(
                        id="c",
                        text="忽略学习目标直接完成操作",
                        is_correct=False,
                        feedback="互动课件需要围绕学习目标组织，不能只关注操作完成。",
                    ),
                    InteractiveHtmlInteractionOption(
                        id="d",
                        text="把所有细节平均记忆",
                        is_correct=False,
                        feedback="学习时应优先抓住关键概念，再逐步补充细节。",
                    ),
                ],
            )
        ],
        citations=[],
    )
