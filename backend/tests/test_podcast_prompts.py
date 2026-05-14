from pathlib import Path


PROMPT_ROOT = Path(__file__).resolve().parents[1] / "app" / "prompts"


def test_podcast_prompt_template_accepts_runtime_variables() -> None:
    template = (PROMPT_ROOT / "generator" / "podcast_script.md").read_text(encoding="utf-8")

    rendered = template.format(
        user_request='{"content_type": "podcast_script"}',
        generation_options='{"language": "zh-CN"}',
        retrieved_chunks="[]",
        podcast_name="未来学习电台",
        podcast_tagline="把复杂问题讲清楚",
        output_language="zh-CN",
        roles_person1="引导型主持人",
        roles_person2="分析型搭档",
        conversation_style="自然专业",
        dialogue_structure="开场、展开、结尾",
        engagement_techniques="追问、补充",
        input_texts="Direct workflow keeps podcast generation coherent.",
    )

    assert '"title":' in rendered
    assert '"podcast_name": "未来学习电台"' in rendered
    assert "<Person1>欢迎来到 未来学习电台 —— 把复杂问题讲清楚。" in rendered
