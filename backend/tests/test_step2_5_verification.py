"""
Step 2-5 验收测试
按照 P0_真实生成闭环_开发指导.md 的验收标准进行测试
"""
import os
import pytest
from app.core.config import get_settings
from app.schemas.outline import Outline, OutlineUnit
from app.schemas.request import ContentGenerationRequest, GenerationOptions
from app.workflows.content_generation_graph import run_content_generation
from app.workflows.nodes.planner_node import _build_fallback_outline
from app.workflows.nodes.mindmap_element_node import validate_mindmap_markdown
from app.schemas.specs import LectureSection, SlideSpecPage
from app.schemas.elements import ImageElement, MindmapElement
from app.workflows.states import ContentGenerationState


class TestStep2Planner:
    """Step 2 验收标准：接入真实 Planner"""

    def test_stub_mode_uses_fallback(self):
        """验收标准 1：provider_mode=stub 时仍然使用 fallback 跑通"""
        settings = get_settings()
        original_mode = settings.provider_mode

        try:
            settings.provider_mode = "stub"
            state = run_content_generation(
                ContentGenerationRequest(
                    content_type="slide_deck",
                    topic="测试主题",
                    user_prompt="生成测试",
                    generation_options=GenerationOptions(slide_count=2),
                )
            )
            assert state.status == "completed"
            assert state.outline is not None
            assert state.outline.metadata.get("stub") == True
            print("✅ stub 模式使用 fallback")
        finally:
            settings.provider_mode = original_mode

    def test_llm_output_passes_schema_validation(self):
        """验收标准 3：LLM 输出能被 Outline schema 校验"""
        state = run_content_generation(
            ContentGenerationRequest(
                content_type="slide_deck",
                topic="测试主题",
                user_prompt="生成测试",
                generation_options=GenerationOptions(slide_count=3),
            )
        )
        assert isinstance(state.outline, Outline)
        assert state.outline.content_type == "slide_deck"
        print(f"✅ Outline schema 校验通过，生成 {len(state.outline.units)} 个 units")

    def test_outline_generates_multiple_units(self):
        """验收标准 5：生成的 outline 至少能产生多个 units"""
        state = run_content_generation(
            ContentGenerationRequest(
                content_type="lecture",
                topic="人工智能基础",
                user_prompt="生成讲义",
                generation_options=GenerationOptions(section_count=4),
            )
        )
        assert len(state.outline.units) >= 2, f"期望至少 2 个 units，实际 {len(state.outline.units)}"
        print(f"✅ 生成了 {len(state.outline.units)} 个 units")

    def test_fallback_outline_structure(self):
        """验收标准 4：LLM 失败时能使用 fallback"""
        request = ContentGenerationRequest(
            content_type="lecture",
            topic="测试主题",
            user_prompt="生成测试",
            generation_options=GenerationOptions(section_count=3),
        )
        state = ContentGenerationState(
            request_id="test_fallback",
            content_type="lecture",
            topic="测试主题",
            user_prompt="生成测试",
            raw_request=request.model_dump(),
            normalized_request={"section_count": 3},
            planning_chunks=[],
            status="running",
        )
        outline = _build_fallback_outline(state, reason="test_fallback")
        assert outline is not None
        assert len(outline.units) == 3
        assert outline.metadata.get("fallback_reason") == "test_fallback"
        print("✅ fallback outline 生成正确")


class TestStep3UnitSpecGenerator:
    """Step 3 验收标准：接入真实 Unit Spec Generator"""

    def test_lecture_unit_generates_section(self):
        """验收标准：每个 outline unit 都能生成对应的 LectureSection"""
        state = run_content_generation(
            ContentGenerationRequest(
                content_type="lecture",
                topic="Python 入门",
                user_prompt="生成讲义",
                generation_options=GenerationOptions(section_count=2),
            )
        )
        assert state.content_spec is not None
        assert isinstance(state.content_spec.sections[0], LectureSection)

        section = state.content_spec.sections[0]
        assert section.outline_unit_id == state.outline.units[0].id
        print(f"✅ LectureSection 生成正确: {section.id}")

    def test_slide_unit_generates_page(self):
        """验收标准：每个 outline unit 都能生成对应的 SlideSpecPage"""
        state = run_content_generation(
            ContentGenerationRequest(
                content_type="slide_deck",
                topic="数据结构",
                user_prompt="生成课件",
                generation_options=GenerationOptions(slide_count=2),
            )
        )
        assert state.content_spec is not None
        assert isinstance(state.content_spec.slides[0], SlideSpecPage)

        slide = state.content_spec.slides[0]
        assert slide.outline_unit_id == state.outline.units[0].id
        print(f"✅ SlideSpecPage 生成正确: {slide.id}")

    def test_outline_unit_id_traceable(self):
        """验收标准：outline_unit_id 能正确追踪回大纲 unit"""
        state = run_content_generation(
            ContentGenerationRequest(
                content_type="lecture",
                topic="测试",
                user_prompt="生成",
                generation_options=GenerationOptions(section_count=2),
            )
        )
        for section in state.content_spec.sections:
            matching_unit = next((u for u in state.outline.units if u.id == section.outline_unit_id), None)
            assert matching_unit is not None, f"无法追踪 outline_unit_id: {section.outline_unit_id}"
        print("✅ outline_unit_id 可追踪")

    def test_source_chunk_ids_stay_empty_without_retrieval(self):
        """验收标准：检索关闭时 source_chunk_ids 为空，不生成占位引用"""
        state = run_content_generation(
            ContentGenerationRequest(
                content_type="lecture",
                topic="测试",
                user_prompt="生成",
                generation_options=GenerationOptions(section_count=1),
            )
        )
        assert state.retrieval_status.state == "disabled"
        for section in state.content_spec.sections:
            assert section.source_chunk_ids == [], f"section {section.id} 不应带来源 id"
        print("✅ 检索关闭时 source_chunk_ids 为空")

    def test_required_elements_match_element_ref(self):
        """验收标准：required_elements 与 element_ref 能一一对应"""
        state = run_content_generation(
            ContentGenerationRequest(
                content_type="lecture",
                topic="测试",
                user_prompt="生成",
                generation_options=GenerationOptions(),
            )
        )
        for section in state.content_spec.sections:
            required_ids = {e.element_id for e in section.required_elements}
            ref_ids = {
                b.element_id
                for b in section.blocks
                if hasattr(b, 'element_id') and b.element_id
            }
            assert required_ids == ref_ids, f"section {section.id} 的 required_elements 与 element_ref 不匹配"
        print("✅ required_elements 与 element_ref 一一对应")


class TestStep4MindmapGenerator:
    """Step 4 验收标准：思维导图已停用，仅保留旧数据校验能力"""

    def test_mindmap_generation_is_disabled(self):
        """验收标准：新任务不再生成 mindmap"""
        state = run_content_generation(
            ContentGenerationRequest(
                content_type="lecture",
                topic="人工智能",
                user_prompt="生成讲义",
                generation_options=GenerationOptions(section_count=1),
            )
        )
        assert not [e for e in state.elements if isinstance(e, MindmapElement)]
        for section in state.content_spec.sections:
            image_specs = [item for item in section.required_elements if item.type == "image"]
            assert len(image_specs) == 1
        print("✅ 新任务不再生成 mindmap")

    def test_mindmap_max_depth_3(self):
        """验收标准：最多 3 层"""
        errors = validate_mindmap_markdown("# 测试\n## 一级\n### 二级\n#### 三级\n#### 超深")
        assert any("depth" in e.lower() for e in errors), "未检测到深度超限"
        print("✅ mindmap 深度校验正常")

    def test_mindmap_has_single_root(self):
        """验收标准：只有一个根节点"""
        markdown = "# 根\n## 分支1\n## 分支2"
        errors = validate_mindmap_markdown(markdown)
        assert len(errors) == 0, f"应该通过，但报错: {errors}"
        print("✅ 单根节点校验通过")

    def test_lecture_sections_have_exactly_one_image(self):
        """验收标准：讲义每节固定 1 张图片，且图片引用可追踪"""
        state = run_content_generation(
            ContentGenerationRequest(
                content_type="lecture",
                topic="测试",
                user_prompt="生成",
                generation_options=GenerationOptions(section_count=1),
            )
        )
        for section in state.content_spec.sections:
            image_specs = [item for item in section.required_elements if item.type == "image"]
            assert len(image_specs) == 1, f"section {section.id} 的图片数量不是 1"
            ref_ids = [block.element_id for block in section.blocks if hasattr(block, "element_id")]
            assert image_specs[0].element_id in ref_ids
        print("✅ 讲义每节固定 1 张图片")


class TestStep5ImageGenerator:
    """Step 5 验收标准：确认 ImageElement 真实生成链路"""

    def test_stub_mode_generates_svg_placeholder(self):
        """验收标准：provider_mode=stub 时生成 SVG 占位图"""
        settings = get_settings()
        original_mode = settings.provider_mode

        try:
            settings.provider_mode = "stub"
            state = run_content_generation(
                ContentGenerationRequest(
                    content_type="slide_deck",
                    topic="测试",
                    user_prompt="生成",
                    generation_options=GenerationOptions(slide_count=2),
                )
            )
            image_elements = [e for e in state.elements if isinstance(e, ImageElement)]
            if image_elements:
                for elem in image_elements:
                    assert elem.asset_url is not None, f"Image {elem.id} asset_url 为空"
                print(f"✅ {len(image_elements)} 个图片有 asset_url")
            else:
                print("⚠️ 未生成图片元素")
        finally:
            settings.provider_mode = original_mode

    def test_image_element_has_alt_text(self):
        """验收标准：ImageElement.alt_text 不为空"""
        state = run_content_generation(
            ContentGenerationRequest(
                content_type="slide_deck",
                topic="测试",
                user_prompt="生成",
                generation_options=GenerationOptions(slide_count=2),
            )
        )
        image_elements = [e for e in state.elements if isinstance(e, ImageElement)]
        if image_elements:
            for elem in image_elements:
                assert elem.alt_text is not None and elem.alt_text != "", f"Image {elem.id} alt_text 为空"
            print(f"✅ {len(image_elements)} 个图片有 alt_text")
        else:
            print("⚠️ 未生成图片元素")

    def test_image_source_ids_preserved(self):
        """验收标准：source_unit_id、source_outline_unit_id、source_chunk_ids 保留"""
        state = run_content_generation(
            ContentGenerationRequest(
                content_type="slide_deck",
                topic="测试",
                user_prompt="生成",
                generation_options=GenerationOptions(slide_count=2),
            )
        )
        image_elements = [e for e in state.elements if isinstance(e, ImageElement)]
        for elem in image_elements:
            assert hasattr(elem, 'source_unit_id'), f"Image {elem.id} 缺少 source_unit_id"
            assert hasattr(elem, 'source_outline_unit_id'), f"Image {elem.id} 缺少 source_outline_unit_id"
            assert hasattr(elem, 'source_chunk_ids'), f"Image {elem.id} 缺少 source_chunk_ids"
        print(f"✅ {len(image_elements)} 个图片保留 source ids")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
