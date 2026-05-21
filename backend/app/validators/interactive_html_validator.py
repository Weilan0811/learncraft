"""
P0 interactive_html validator: checks block legality, interaction structure,
and section completeness.
"""

from app.schemas.specs.interactive_html import (
    InteractiveHtmlSectionSpec,
    InteractiveHtmlSpec,
    SingleChoiceBlock,
    MultipleChoiceBlock,
    ShortAnswerBlock,
    DragMatchBlock,
    SequenceBlock,
    SocraticChatBlock,
    ScenarioBlock,
)


class InteractiveHtmlValidationIssue:
    def __init__(self, path: str, message: str):
        self.path = path
        self.message = message


class InteractiveHtmlValidationReport:
    def __init__(self, ok: bool, issues: list[InteractiveHtmlValidationIssue]):
        self.ok = ok
        self.issues = issues


def _valid_block_types() -> set[str]:
    return {
        "heading", "paragraph", "concept_card", "callout", "example", "summary",
        "animated_flow", "case_compare", "context_inspector", "stepper",
        "single_choice", "multiple_choice", "short_answer", "drag_match", "sequence", "flashcard",
        "socratic_chat", "scenario",
    }


def validate_unit_spec(section: InteractiveHtmlSectionSpec) -> InteractiveHtmlValidationReport:
    """Validate a single InteractiveHtmlSectionSpec."""
    issues: list[InteractiveHtmlValidationIssue] = []

    if not section.section_id:
        issues.append(InteractiveHtmlValidationIssue("section_id", "section_id is missing"))
    if not section.title:
        issues.append(InteractiveHtmlValidationIssue("title", "title is missing"))
    if not section.learning_goal:
        issues.append(InteractiveHtmlValidationIssue("learning_goal", "learning_goal is missing"))
    if not section.blocks:
        issues.append(InteractiveHtmlValidationIssue("blocks", "blocks must not be empty"))
        return InteractiveHtmlValidationReport(ok=False, issues=issues)

    valid_types = _valid_block_types()
    for i, block in enumerate(section.blocks):
        prefix = f"blocks[{i}]"

        if block.type not in valid_types:
            issues.append(InteractiveHtmlValidationIssue(
                f"{prefix}.type", f"unknown block type: {block.type}"
            ))
            continue

        if not block.block_id:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.block_id", "block_id is missing"))

        # Validate interactive blocks
        _validate_interaction(block, prefix, issues)

    return InteractiveHtmlValidationReport(ok=len(issues) == 0, issues=issues)


def _validate_interaction(block, prefix: str, issues: list[InteractiveHtmlValidationIssue]) -> None:
    bt = block.type

    if bt == "single_choice":
        sc = block  # type: SingleChoiceBlock
        if not sc.question:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.question", "single_choice question is missing"))
        if not sc.options:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.options", "single_choice options are empty"))
        else:
            correct = [o for o in sc.options if o.is_correct]
            if len(correct) != 1:
                issues.append(InteractiveHtmlValidationIssue(
                    f"{prefix}.options", f"single_choice must have exactly 1 correct option, found {len(correct)}"
                ))
        if not sc.explanation:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.explanation", "single_choice explanation is missing"))
        if not sc.interaction_id:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.interaction_id", "interaction_id is missing"))

    elif bt == "multiple_choice":
        mc = block  # type: MultipleChoiceBlock
        if not mc.question:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.question", "multiple_choice question is missing"))
        if not mc.options:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.options", "multiple_choice options are empty"))
        else:
            correct = [o for o in mc.options if o.is_correct]
            if not correct:
                issues.append(InteractiveHtmlValidationIssue(
                    f"{prefix}.options", "multiple_choice must have at least 1 correct option"
                ))
        if not mc.explanation:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.explanation", "multiple_choice explanation is missing"))
        if not mc.interaction_id:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.interaction_id", "interaction_id is missing"))

    elif bt == "short_answer":
        sa = block  # type: ShortAnswerBlock
        if not sa.question:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.question", "short_answer question is missing"))
        if not sa.reference_points:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.reference_points", "short_answer reference_points is empty"))
        if not sa.interaction_id:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.interaction_id", "interaction_id is missing"))

    elif bt == "drag_match":
        dm = block  # type: DragMatchBlock
        if not dm.instruction:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.instruction", "drag_match instruction is missing"))
        if not dm.items:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.items", "drag_match items are empty"))
        if not dm.targets:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.targets", "drag_match targets are empty"))
        if not dm.explanation:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.explanation", "drag_match explanation is missing"))
        if not dm.interaction_id:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.interaction_id", "interaction_id is missing"))

    elif bt == "sequence":
        sq = block  # type: SequenceBlock
        if not sq.instruction:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.instruction", "sequence instruction is missing"))
        if not sq.items:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.items", "sequence items are empty"))
        if not sq.explanation:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.explanation", "sequence explanation is missing"))
        if not sq.interaction_id:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.interaction_id", "interaction_id is missing"))

    elif bt == "socratic_chat":
        sc_chat = block  # type: SocraticChatBlock
        if not sc_chat.goal:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.goal", "socratic_chat goal is missing"))
        if not sc_chat.rounds:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.rounds", "socratic_chat rounds are empty"))
        if not sc_chat.interaction_id:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.interaction_id", "interaction_id is missing"))

    elif bt == "scenario":
        sn = block  # type: ScenarioBlock
        if not sn.scenario_title:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.scenario_title", "scenario_title is missing"))
        if not sn.background:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.background", "scenario background is missing"))
        if not sn.scenes:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.scenes", "scenario scenes are empty"))
        if not sn.interaction_id:
            issues.append(InteractiveHtmlValidationIssue(f"{prefix}.interaction_id", "interaction_id is missing"))


def validate_content(spec: InteractiveHtmlSpec) -> InteractiveHtmlValidationReport:
    """Validate a complete InteractiveHtmlSpec."""
    issues: list[InteractiveHtmlValidationIssue] = []

    if not spec.lesson_id:
        issues.append(InteractiveHtmlValidationIssue("lesson_id", "lesson_id is missing"))
    if not spec.title:
        issues.append(InteractiveHtmlValidationIssue("title", "title is missing"))
    if not spec.sections:
        issues.append(InteractiveHtmlValidationIssue("sections", "spec must have at least one section"))
    else:
        section_ids = [s.section_id for s in spec.sections]
        if len(section_ids) != len(set(section_ids)):
            issues.append(InteractiveHtmlValidationIssue("sections", "section ids must be unique"))

        for section in spec.sections:
            report = validate_unit_spec(section)
            for issue in report.issues:
                issues.append(InteractiveHtmlValidationIssue(
                    f"section {section.section_id}/{issue.path}", issue.message
                ))

    return InteractiveHtmlValidationReport(ok=len(issues) == 0, issues=issues)
