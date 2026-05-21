"""
Validator and sanitizer for constrained interactive_html fragments.

P0 refactor: split into three concerns:
- validate_unit_spec: validates InteractiveHtmlSectionSpec (teaching design, no HTML)
- validate_rendered_unit: validates InteractiveHtmlRenderedUnit (HTML + CSS + manifest)
- sanitize_rendered_unit: cleans HTML + CSS in rendered unit
- sanitize_html_fragment: legacy sanitizer for backward compatibility
- validate_content: validates full InteractiveHtmlSpec
"""

from html.parser import HTMLParser
import re

import bleach

from app.schemas.render.interactive_html import InteractiveHtmlRenderedUnit
from app.schemas.specs.interactive_html import InteractiveHtmlSectionSpec, InteractiveHtmlSpec


ALLOWED_TAGS = {
    "section", "div", "article", "header", "footer", "aside", "nav",
    "h2", "h3", "h4", "p", "ul", "ol", "li",
    "strong", "em", "span", "button", "input", "textarea", "label",
    "br", "code", "pre",
}
FORBIDDEN_FULL_PAGE_TAGS = {"html", "head", "body"}
FORBIDDEN_TAGS = {"script", "style", "iframe", "object", "embed", "link", "meta", "svg"}
ALLOWED_ATTRS = {
    "class", "id", "role", "type", "value", "checked", "disabled", "placeholder",
    "name", "aria-label", "aria-live", "aria-expanded", "aria-controls",
    "aria-describedby",
    "data-ih-action", "data-section-id", "data-interaction-id", "data-option-id",
    "data-target-id", "data-item-id", "data-tab-target", "data-flow-id", "data-step",
    "data-block-id", "data-block-type", "data-tab-panel", "data-correct",
    "data-feedback-for", "data-state", "data-role",
}
INTERACTION_ACTIONS = {
    "single-choice",
    "multiple-choice",
    "short-answer",
    "sequence-select",
    "match-select",
    "complete-section",
    "tab-select",
    "flow-next",
    "flow-prev",
    "flow-reset",
}
INTERACTION_ACTION_ALIASES = {
    "toggle_selection": "multiple-choice",
    "check_answer": "single-choice",
}
ALLOWED_TEACHING_BLOCK_TYPES = {
    "intro",
    "concept_explanation",
    "case_compare",
    "animated_flow",
    "context_inspector",
    "stepper",
    "socratic_chat",
    "scenario",
    "single_choice",
    "multiple_choice",
    "short_answer",
    "drag_match",
    "sequence",
    "reflection",
    "summary",
}
ALLOWED_RENDER_BLOCK_TYPES = {
    "intro",
    "concept",
    "explain",
    "visual",
    "case_compare",
    "flow",
    "tabs",
    "scenario",
    "dialogue",
    "quiz",
    "practice",
    "reflection",
    "summary",
}
INTERACTIVE_BLOCK_TYPES = {"quiz", "practice", "scenario", "dialogue", "single_choice", "multiple_choice", "short_answer", "drag_match", "sequence", "socratic_chat"}
EXPLANATORY_BLOCK_TYPES = {"intro", "concept", "explain", "visual", "case_compare", "flow", "tabs", "concept_explanation", "animated_flow", "context_inspector", "stepper"}
COURSEWARE_CLASS_MARKERS = {
    "ih-card",
    "ih-concept-grid",
    "ih-flow-board",
    "ih-tabs",
    "ih-quiz",
    "ih-dialogue-panel",
    "ih-scenario-layout",
    "ih-reflection",
}


class InteractiveHtmlValidationIssue:
    def __init__(self, path: str, message: str):
        self.path = path
        self.message = message


class InteractiveHtmlValidationReport:
    def __init__(self, ok: bool, issues: list[InteractiveHtmlValidationIssue]):
        self.ok = ok
        self.issues = issues


class _FragmentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root_tags: list[tuple[str, dict[str, str]]] = []
        self.stack: list[str] = []
        self.node_stack: list[tuple[str, str | None]] = []
        self.block_stack: list[str] = []
        self.blocks: list[dict[str, str]] = []
        self.tags: list[str] = []
        self.attrs: list[tuple[str, str, str]] = []
        self.text_parts: list[str] = []
        self.interaction_ids: set[str] = set()
        self.interaction_id_list: list[str] = []
        self.interaction_to_block: dict[str, str] = {}
        self.actions: set[str] = set()
        self.class_names: set[str] = set()
        self.heading_count = 0
        self.paragraph_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {name: value or "" for name, value in attrs}
        if not self.stack:
            self.root_tags.append((tag, attr_dict))
        block_id = attr_dict.get("data-block-id", "")
        started_block = block_id or None
        if block_id:
            self.block_stack.append(block_id)
            self.blocks.append(
                {
                    "block_id": block_id,
                    "type": attr_dict.get("data-block-type", ""),
                    "tag": tag,
                    "class": attr_dict.get("class", ""),
                }
            )
        self.stack.append(tag)
        self.node_stack.append((tag, started_block))
        self.tags.append(tag)
        for class_name in attr_dict.get("class", "").split():
            self.class_names.add(class_name)
        if tag in {"h2", "h3", "h4"}:
            self.heading_count += 1
        if tag == "p":
            self.paragraph_count += 1
        for name, value in attr_dict.items():
            self.attrs.append((tag, name, value))
            if name == "data-interaction-id" and value:
                self.interaction_ids.add(value)
                self.interaction_id_list.append(value)
                if self.block_stack:
                    self.interaction_to_block[value] = self.block_stack[-1]
            if name == "data-ih-action" and value:
                self.actions.add(value)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.stack:
            while self.stack:
                current = self.stack.pop()
                if self.node_stack:
                    _, started_block = self.node_stack.pop()
                    if started_block and self.block_stack and self.block_stack[-1] == started_block:
                        self.block_stack.pop()
                if current == tag:
                    break

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.text_parts.append(data.strip())


def sanitize_html_fragment(fragment: str) -> str:
    """Clean an LLM-generated unit fragment with a strict teaching HTML whitelist."""

    fragment = _normalize_interaction_action_aliases(fragment)
    return bleach.clean(
        fragment,
        tags=ALLOWED_TAGS,
        attributes=_allowed_attr,
        protocols=[],
        strip=True,
        strip_comments=True,
    ).strip()


def validate_unit_spec(section: InteractiveHtmlSectionSpec) -> InteractiveHtmlValidationReport:
    issues: list[InteractiveHtmlValidationIssue] = []

    if not section.section_id:
        issues.append(InteractiveHtmlValidationIssue("section_id", "section_id is missing"))
    if not section.title:
        issues.append(InteractiveHtmlValidationIssue("title", "title is missing"))
    if not section.learning_goal:
        issues.append(InteractiveHtmlValidationIssue("learning_goal", "learning_goal is missing"))

    block_ids = [block.block_id for block in section.teaching_flow]
    if len(block_ids) != len(set(block_ids)):
        issues.append(InteractiveHtmlValidationIssue("teaching_flow", "block_id values must be unique"))

    if not 3 <= len(section.teaching_flow) <= 7:
        issues.append(InteractiveHtmlValidationIssue("teaching_flow", "teaching_flow should contain 3-7 teaching blocks"))

    unknown_types = sorted({
        block.block_type for block in section.teaching_flow
        if block.block_type not in ALLOWED_TEACHING_BLOCK_TYPES
    })
    if unknown_types:
        issues.append(InteractiveHtmlValidationIssue("teaching_flow", f"unsupported block_type values: {unknown_types}"))

    for block in section.teaching_flow:
        if not block.content_goal.strip():
            issues.append(InteractiveHtmlValidationIssue(f"teaching_flow/{block.block_id}", "content_goal is required"))
        if len(block.title.strip()) < 4:
            issues.append(InteractiveHtmlValidationIssue(f"teaching_flow/{block.block_id}", "title should be specific"))

    has_explanatory = any(
        block.block_type in EXPLANATORY_BLOCK_TYPES for block in section.teaching_flow
    )
    if not has_explanatory:
        issues.append(InteractiveHtmlValidationIssue("teaching_flow", "unit should include explanatory teaching content"))

    interaction_ids = [spec.interaction_id for spec in section.interaction_specs]
    if len(interaction_ids) != len(set(interaction_ids)):
        issues.append(InteractiveHtmlValidationIssue("interaction_specs", "interaction_id values must be unique"))

    spec_block_ids = {block.block_id for block in section.teaching_flow}
    for spec in section.interaction_specs:
        if spec.block_id not in spec_block_ids:
            issues.append(InteractiveHtmlValidationIssue(f"interaction_specs/{spec.interaction_id}", f"block_id '{spec.block_id}' does not exist in teaching_flow"))

    interactive_block_ids = {
        block.block_id for block in section.teaching_flow
        if block.block_type in INTERACTIVE_BLOCK_TYPES
    }
    for block in section.teaching_flow:
        if block.interaction_id and block.interaction_id not in interaction_ids:
            issues.append(InteractiveHtmlValidationIssue(f"teaching_flow/{block.block_id}", f"interaction_id '{block.interaction_id}' not found in interaction_specs"))

    return InteractiveHtmlValidationReport(ok=len(issues) == 0, issues=issues)


def validate_rendered_unit(unit: InteractiveHtmlRenderedUnit) -> InteractiveHtmlValidationReport:
    issues: list[InteractiveHtmlValidationIssue] = []

    if not unit.section_id:
        issues.append(InteractiveHtmlValidationIssue("section_id", "section_id is missing"))
    if not unit.title:
        issues.append(InteractiveHtmlValidationIssue("title", "title is missing"))
    if not unit.learning_goal:
        issues.append(InteractiveHtmlValidationIssue("learning_goal", "learning_goal is missing"))
    if not unit.style_scope_id:
        issues.append(InteractiveHtmlValidationIssue("style_scope_id", "style_scope_id is missing"))

    _validate_rendered_html(unit, issues)
    _validate_rendered_css(unit, issues)
    _validate_manifest_consistency(unit, issues)

    return InteractiveHtmlValidationReport(ok=len(issues) == 0, issues=issues)


def sanitize_rendered_unit(unit: InteractiveHtmlRenderedUnit) -> InteractiveHtmlRenderedUnit:
    sanitized_html = sanitize_html_fragment(unit.html_fragment)
    sanitized_css = _sanitize_css_fragment(unit.css_fragment)
    return unit.model_copy(update={
        "html_fragment": sanitized_html,
        "css_fragment": sanitized_css,
    })


def validate_content(spec: InteractiveHtmlSpec) -> InteractiveHtmlValidationReport:
    issues: list[InteractiveHtmlValidationIssue] = []

    if not spec.lesson_id:
        issues.append(InteractiveHtmlValidationIssue("lesson_id", "lesson_id is missing"))
    if not spec.title:
        issues.append(InteractiveHtmlValidationIssue("title", "title is missing"))
    if not spec.sections:
        issues.append(InteractiveHtmlValidationIssue("sections", "spec must have at least one section"))
        return InteractiveHtmlValidationReport(ok=False, issues=issues)

    section_ids = [section.section_id for section in spec.sections]
    if len(section_ids) != len(set(section_ids)):
        issues.append(InteractiveHtmlValidationIssue("sections", "section ids must be unique"))

    for section in spec.sections:
        report = validate_unit_spec(section)
        for issue in report.issues:
            issues.append(InteractiveHtmlValidationIssue(f"section {section.section_id}/{issue.path}", issue.message))

    return InteractiveHtmlValidationReport(ok=len(issues) == 0, issues=issues)


def _validate_rendered_html(unit: InteractiveHtmlRenderedUnit, issues: list[InteractiveHtmlValidationIssue]) -> None:
    if not unit.html_fragment.strip():
        issues.append(InteractiveHtmlValidationIssue("html_fragment", "html_fragment is missing"))
        return

    parser = _parse(unit.html_fragment)
    lower_fragment = unit.html_fragment.lower()

    if any(re.search(rf"<\s*{tag}\b", lower_fragment) for tag in FORBIDDEN_FULL_PAGE_TAGS):
        issues.append(InteractiveHtmlValidationIssue("html_fragment", "html_fragment must not include full-page tags"))

    forbidden = sorted(FORBIDDEN_TAGS & set(parser.tags))
    if forbidden:
        issues.append(InteractiveHtmlValidationIssue("html_fragment", f"html_fragment includes forbidden tags: {forbidden}"))

    if len(parser.root_tags) != 1 or parser.root_tags[0][0] != "section":
        issues.append(InteractiveHtmlValidationIssue("html_fragment", "html_fragment must have a single root section"))
    else:
        root_attrs = parser.root_tags[0][1]
        if root_attrs.get("id") != unit.section_id:
            issues.append(InteractiveHtmlValidationIssue("html_fragment", "root section id must match section_id"))
        if unit.style_scope_id not in root_attrs.get("class", ""):
            issues.append(InteractiveHtmlValidationIssue("html_fragment", "root section must include style_scope_id in class"))

    if parser.heading_count < 1 or parser.paragraph_count < 1 or len("".join(parser.text_parts)) < 30:
        issues.append(InteractiveHtmlValidationIssue("html_fragment", "html_fragment should include heading and paragraph content"))

    for tag, name, value in parser.attrs:
        if name.lower().startswith("on"):
            issues.append(InteractiveHtmlValidationIssue("html_fragment", "html_fragment must not include inline event handlers"))
        if value.strip().lower().startswith("javascript:"):
            issues.append(InteractiveHtmlValidationIssue("html_fragment", "html_fragment must not include javascript: URLs"))
        if name == "data-ih-action" and value not in INTERACTION_ACTIONS:
            issues.append(InteractiveHtmlValidationIssue("html_fragment", f"unsupported data-ih-action: {value}"))


def _validate_rendered_css(unit: InteractiveHtmlRenderedUnit, issues: list[InteractiveHtmlValidationIssue]) -> None:
    if not unit.css_fragment.strip():
        issues.append(InteractiveHtmlValidationIssue("css_fragment", "css_fragment is missing"))
        return

    css = unit.css_fragment
    if "@import" in css:
        issues.append(InteractiveHtmlValidationIssue("css_fragment", "css_fragment must not include @import"))
    if re.search(r"url\s*\(\s*['\"]?https?://", css):
        issues.append(InteractiveHtmlValidationIssue("css_fragment", "css_fragment must not include external URLs"))
    if "position:" in css and "fixed" in css:
        issues.append(InteractiveHtmlValidationIssue("css_fragment", "css_fragment must not use position: fixed"))

    z_indices = re.findall(r"z-index\s*:\s*(\d+)", css)
    for z in z_indices:
        if int(z) > 20:
            issues.append(InteractiveHtmlValidationIssue("css_fragment", f"z-index value {z} exceeds maximum of 20"))

    global_selectors = re.findall(r"^(?:body|html|:root)\s*[{,]", css, re.MULTILINE)
    if global_selectors:
        issues.append(InteractiveHtmlValidationIssue("css_fragment", "css_fragment must not use global selectors (body, html, :root)"))

    bare_selectors = re.findall(r"^(?:button|div|section)\s*[{,]", css, re.MULTILINE)
    if bare_selectors:
        issues.append(InteractiveHtmlValidationIssue("css_fragment", "css_fragment must not use unscoped element selectors"))


def _validate_manifest_consistency(unit: InteractiveHtmlRenderedUnit, issues: list[InteractiveHtmlValidationIssue]) -> None:
    if not unit.html_fragment.strip():
        return

    parser = _parse(unit.html_fragment)

    dom_block_ids = {block["block_id"] for block in parser.blocks}
    manifest_block_ids = {ref.block_id for ref in unit.block_manifest}
    if dom_block_ids != manifest_block_ids:
        issues.append(InteractiveHtmlValidationIssue("block_manifest", "block_manifest must match data-block-id values in html_fragment"))

    manifest_interaction_ids = {ref.interaction_id for ref in unit.interaction_manifest}
    if parser.interaction_ids != manifest_interaction_ids:
        issues.append(InteractiveHtmlValidationIssue("interaction_manifest", "interaction_manifest must match data-interaction-id values in html_fragment"))


def _sanitize_css_fragment(css: str) -> str:
    css = re.sub(r"@import[^;]*;", "", css)
    css = re.sub(r"url\s*\(\s*['\"]?https?://[^)]*\)", "", css)
    return css.strip()


def _normalize_interaction_action_aliases(fragment: str) -> str:
    for alias, action in INTERACTION_ACTION_ALIASES.items():
        fragment = re.sub(
            rf'(data-ih-action\s*=\s*["\']){re.escape(alias)}(["\'])',
            rf"\1{action}\2",
            fragment,
        )
    return fragment


def _allowed_attr(tag: str, name: str, value: str) -> bool:
    if name.lower().startswith("on"):
        return False
    if value.strip().lower().startswith("javascript:"):
        return False
    if name in ALLOWED_ATTRS:
        return True
    return name.startswith("aria-") or name.startswith("data-ih-")


def _parse(fragment: str) -> _FragmentParser:
    parser = _FragmentParser()
    parser.feed(fragment)
    parser.close()
    return parser
