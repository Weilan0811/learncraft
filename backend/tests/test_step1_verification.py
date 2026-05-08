from app.schemas.request import ContentGenerationRequest, GenerationOptions


def test_step1_generation_options_accepts_new_fields():
    request = ContentGenerationRequest(
        content_type="lecture",
        topic="人工智能基础导论",
        user_prompt="生成讲义",
        generation_options=GenerationOptions(
            language="zh-CN",
            audience="大学生",
            difficulty="introductory",
            style="educational",
            duration_minutes=30,
            section_count=5,
            slide_count=None,
            output_depth="detailed",
            include_images=True,
            include_charts=False,
            include_mindmap=True,
            image_style="真实感",
            citation_policy="strict",
            slide_theme=None,
            speaker_notes=True,
            pdf_options={"page_size": "A4"},
        )
    )
    assert request.generation_options.audience == "大学生"
    assert request.generation_options.duration_minutes == 30
    assert request.generation_options.include_mindmap == True
    print("✅ ContentGenerationRequest 可以接收新增字段")


def test_step1_old_request_without_options():
    request = ContentGenerationRequest(
        content_type="slide_deck",
        topic="Python入门",
        user_prompt="生成课件",
    )
    assert request.generation_options.slide_count == 6
    print("✅ 无新增字段的旧请求仍能跑通，默认值正确")


def test_step1_normalize_request_includes_all_fields():
    request = ContentGenerationRequest(
        content_type="lecture",
        topic="测试主题",
        user_prompt="测试",
        generation_options=GenerationOptions(
            audience="中学生",
            duration_minutes=25,
        )
    )
    assert request.generation_options.audience == "中学生"
    assert request.generation_options.duration_minutes == 25
    assert request.generation_options.include_mindmap == False
    print("✅ 所有新字段都能正确设置")


if __name__ == "__main__":
    test_step1_generation_options_accepts_new_fields()
    test_step1_old_request_without_options()
    test_step1_normalize_request_includes_all_fields()
    print("\n🎉 Step 1 验收标准全部通过！")
