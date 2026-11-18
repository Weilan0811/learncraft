from pathlib import Path

from app.schemas.request import AttachmentDoc, ContentGenerationRequest
from app.services.local_kb_service import LocalKBService


def test_explicit_queries_search_real_materials_separately_and_preserve_provenance():
    root = Path(__file__).resolve().parents[2]
    material = (root / "knowledge/examples/workbench-guide.md").read_text(encoding="utf-8")
    request = ContentGenerationRequest(
        content_type="interactive_html",
        topic="教学内容工作台使用说明",
        user_prompt="介绍创建任务和学习记录的使用方法。",
        kb_mode="materials_only",
        attachments=[AttachmentDoc(filename="workbench-guide.md", content=material)],
    )
    queries = ["图片或语音失败时怎样重试资源", "互动讲义的学习事件和答题记录怎样保存"]
    service = LocalKBService(method="keyword")
    result = service.retrieve(request, "generation", queries=[*queries, queries[0]])

    assert result.status.state == "ok"
    assert result.queries == queries
    assert [row["query"] for row in result.query_results] == queries
    assert all(row["chunk_ids"] for row in result.query_results)
    assert len({chunk.id for chunk in result.chunks}) == len(result.chunks)
    assert any("资源重试" in chunk.content for chunk in result.chunks)
    assert any("学习事件" in chunk.content for chunk in result.chunks)
    assert all(set(chunk.metadata["matched_queries"]) <= set(queries) for chunk in result.chunks)
    assert service._chunks is None
