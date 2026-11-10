from types import SimpleNamespace

from app.services.adaptive_brief_service import load_lesson_context


class FakeRepository:
    def __init__(self, task, artifacts: dict[tuple[str, str], object]) -> None:
        self._task = task
        self._artifacts = artifacts

    def get_task(self, task_id: str):
        return self._task if task_id == "task_1" else None

    def get_latest_artifact(self, task_id: str, artifact_type: str):
        return self._artifacts.get((task_id, artifact_type))


def _spec_payload() -> dict:
    return {
        "content_type": "interactive_html",
        "lesson_id": "lesson_task_1",
        "title": "提示工程入门",
        "meta": {"language": "zh-CN", "audience": "初学者", "difficulty": "intermediate"},
        "sections": [
            {
                "section_id": "s1",
                "title": "第一节 基础",
                "learning_goal": "理解提示结构",
                "teaching_flow": [
                    {
                        "block_id": "b1",
                        "block_type": "single_choice",
                        "title": "小测",
                        "teaching_role": "check",
                        "content_goal": "检查理解",
                        "interaction_id": "i1",
                    }
                ],
                "interaction_specs": [
                    {
                        "interaction_id": "i1",
                        "block_id": "b1",
                        "type": "single_choice",
                        "event_type": "single_choice_answered",
                        "target_concepts": ["提示结构", "角色设定"],
                    }
                ],
            }
        ],
    }


def test_load_lesson_context_reads_spec(monkeypatch) -> None:
    from app.api import content_generation

    artifact = SimpleNamespace(payload=_spec_payload())
    repository = FakeRepository(
        task=SimpleNamespace(topic="提示工程"),
        artifacts={("task_1", "content_spec"): artifact},
    )
    monkeypatch.setattr(content_generation.task_service, "repository", repository)

    context = load_lesson_context("lesson_task_1")

    assert context.title == "提示工程入门"
    assert context.difficulty == "intermediate"
    assert context.section_titles == {"s1": "第一节 基础"}
    assert context.concept_map == {"i1": ["提示结构", "角色设定"]}


def test_load_lesson_context_falls_back_to_render(monkeypatch) -> None:
    from app.api import content_generation

    render_payload = {
        "render_type": "interactive_html_page",
        "lesson_id": "lesson_task_1",
        "title": "渲染标题",
        "sections": [
            {
                "section_id": "s1",
                "title": "第一节",
                "learning_goal": "目标",
                "style_scope_id": "scope_s1",
                "html_fragment": "<p>内容</p>",
                "css_fragment": "",
                "interaction_manifest": [
                    {
                        "interaction_id": "i1",
                        "section_id": "s1",
                        "type": "single_choice",
                        "target_concepts": ["概念A"],
                        "event_type": "single_choice_answered",
                    }
                ],
            }
        ],
    }
    repository = FakeRepository(
        task=SimpleNamespace(topic="任务主题"),
        artifacts={("task_1", "final_render"): SimpleNamespace(payload=render_payload)},
    )
    monkeypatch.setattr(content_generation.task_service, "repository", repository)

    context = load_lesson_context("partial_lesson_task_1")

    assert context.title == "渲染标题"
    assert context.section_titles == {"s1": "第一节"}
    assert context.concept_map == {"i1": ["概念A"]}
