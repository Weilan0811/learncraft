import json
import os
from typing import cast

from pydantic import Field

from app.core.config import get_settings
from app.schemas.base import SchemaModel
from app.schemas.elements import MindmapElement
from app.schemas.specs import ElementRequest
from app.services.llm_service import get_llm_service


class MindmapMarkdownOutput(SchemaModel):
    markdown: str = Field(description="Markmap-compatible markdown. Must start with one # root heading.")


def generate_mindmap_element(state: dict[str, object]) -> dict[str, object]:
    request = ElementRequest.model_validate(state["element_request"])
    settings = get_settings()
    
    if settings.provider_mode == "stub":
        element = _build_fallback_mindmap(request)
    else:
        try:
            element = _generate_mindmap_with_llm(request, state)
        except Exception as exc:
            element = _build_fallback_mindmap(request, reason=str(exc))
    
    return {"current_unit_elements": [element]}


def _generate_mindmap_with_llm(request: ElementRequest, state: dict[str, object]) -> MindmapElement:
    prompt = _build_mindmap_prompt(request, state)
    llm_service = get_llm_service()
    output = cast(MindmapMarkdownOutput, llm_service.generate_structured(prompt=prompt, schema=MindmapMarkdownOutput))
    
    errors = validate_mindmap_markdown(output.markdown)
    if errors:
        raise ValueError(f"Mindmap validation failed: {', '.join(errors)}")
    
    return MindmapElement(
        id=request.element_id,
        title=request.title,
        markdown=output.markdown,
        source_unit_id=request.source_unit_id,
        source_outline_unit_id=request.source_outline_unit_id,
        source_chunk_ids=request.source_chunk_ids,
        metadata={"max_depth": 3, "format": "markmap_markdown", "fallback": False},
        render_hints={"renderer": "markmap", "export_as": ["svg", "png"]},
        generation_info={"generator": "llm_mindmap_markdown"},
    )


def _build_mindmap_prompt(request: ElementRequest, state: dict[str, object]) -> str:
    template_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "generator", "section_elements.md")
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Prompt template not found: {template_path}")
    
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    context_info = json.dumps(request.context, ensure_ascii=False, indent=2)
    
    prompt = f"""你是内容生成 Agent 的 Mindmap Markdown Generator。请根据当前内容单元生成可用于 Markmap 渲染的 Markdown 思维导图。

硬性要求：
- 输出必须能被 MindmapMarkdownOutput schema 校验通过。
- markdown 必须以一级标题 # 开头。
- 只能有一个一级标题。
- 最多 3 层结构。
- 一级分支 3-6 个。
- 每个节点尽量短，适合图形展示。
- 不要输出 HTML。
- 不要输出 Mermaid。
- 不要输出解释文字。
- 不要输出 Markdown 代码块。

推荐格式：
# 根标题
## 一级分支
### 二级节点
### 二级节点
## 一级分支
### 二级节点

输入信息：
- 标题：{request.title}
- 用途：{request.purpose}
- 指令：{request.instruction}
- 上下文：{context_info}

只输出 markdown 内容，不要有其他文字。
"""
    
    return prompt


def validate_mindmap_markdown(markdown: str) -> list[str]:
    errors = []
    lines = [line.rstrip() for line in markdown.splitlines() if line.strip()]
    
    if not lines:
        errors.append("mindmap markdown is empty")
        return errors
    
    if not lines[0].startswith("# "):
        errors.append("mindmap markdown must start with one # root heading")
    
    root_count = sum(1 for line in lines if line.startswith("# ") and not line.startswith("## "))
    if root_count != 1:
        errors.append("mindmap markdown must contain exactly one root heading")
    
    if any(line.startswith("####") for line in lines):
        errors.append("mindmap markdown depth must be <= 3")
    
    if any("<" in line and ">" in line for line in lines):
        errors.append("mindmap markdown must not contain html")
    
    return errors


def _build_fallback_mindmap(request: ElementRequest, reason: str | None = None) -> MindmapElement:
    context = request.context
    key_points = context.get("key_points", [])
    
    if not isinstance(key_points, list) or not key_points:
        key_points = ["核心概念", "应用场景", "学习重点"]
    
    markdown_lines = [f"# {request.title}"]
    for point in key_points[:6]:
        markdown_lines.append(f"## {point}")
    
    markdown = "\n".join(markdown_lines)
    
    metadata = {"max_depth": 3, "format": "markmap_markdown", "fallback": True}
    if reason:
        metadata["fallback_reason"] = reason
    
    return MindmapElement(
        id=request.element_id,
        title=request.title,
        markdown=markdown,
        source_unit_id=request.source_unit_id,
        source_outline_unit_id=request.source_outline_unit_id,
        source_chunk_ids=request.source_chunk_ids,
        metadata=metadata,
        render_hints={"renderer": "markmap", "export_as": ["svg", "png"]},
        generation_info={"generator": "mindmap_fallback"},
    )


__all__ = ["generate_mindmap_element"]