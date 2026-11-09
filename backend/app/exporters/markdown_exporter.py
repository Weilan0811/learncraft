from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import LectureRenderModel, RenderModel
from app.schemas.render.podcast import PodcastRenderModel
from app.services.storage_service import LocalStorageService, StorageService


class MarkdownExporter:
    export_type = "markdown"

    def __init__(self, storage_service: StorageService | None = None) -> None:
        self.storage_service = storage_service or LocalStorageService()

    def export(
        self,
        task_id: str,
        render_model: RenderModel,
        request: ExportRequest,
        asset_ids: list[str] | None = None,
        content_spec: object | None = None,
    ) -> ExportResult:
        if isinstance(render_model, PodcastRenderModel):
            return self._save(
                task_id,
                f"{task_id}_podcast_script",
                request,
                f"# {render_model.title}\n\n{render_model.script_text}\n",
                render_model.render_type,
            )
        if isinstance(render_model, LectureRenderModel):
            return self._save(
                task_id,
                f"{task_id}_lecture",
                request,
                self._lecture_markdown(render_model),
                render_model.render_type,
            )
        return ExportResult(
            export_type=request.export_type,
            file_url="",
            status="failed",
            metadata={"task_id": task_id, "error": "Markdown 导出当前支持讲义和播客文稿。"},
        )

    def _save(
        self,
        task_id: str,
        filename_stem: str,
        request: ExportRequest,
        content: str,
        render_type: str,
    ) -> ExportResult:
        record = self.storage_service.save_bytes(
            asset_id=f"export_{task_id}_markdown",
            filename=f"{filename_stem}.md",
            content=content.encode("utf-8"),
            content_type="text/markdown; charset=utf-8",
            kind="markdown",
            metadata={"task_id": task_id, "render_type": render_type},
        )
        return ExportResult(
            export_type=request.export_type,
            file_url=record.url,
            status="success",
            metadata={"asset_id": record.asset_id, "render_type": render_type, "byte_size": record.byte_size},
        )

    @staticmethod
    def _lecture_markdown(render_model: LectureRenderModel) -> str:
        lines: list[str] = [f"# {render_model.title}", ""]
        if render_model.objectives:
            lines.append("## 学习目标")
            lines.extend(f"- {objective}" for objective in render_model.objectives)
            lines.append("")
        citations: list[str] = []
        for section in render_model.sections:
            lines.extend([f"## {section.title}", ""])
            for block in section.render_blocks:
                if block.type == "image":
                    caption = block.title or block.id
                    lines.append(f"![{caption}]({block.asset_url or ''})")
                    if block.title:
                        lines.extend(["", f"*{block.title}*"])
                    lines.append("")
                    continue
                if block.title:
                    lines.extend([f"### {block.title}", ""])
                if block.content:
                    markers = MarkdownExporter._citation_markers(block.metadata, citations)
                    if block.type == "mindmap":
                        lines.extend(["```markdown", block.content, "```", markers, ""])
                    else:
                        lines.extend([f"{block.content}{markers}", ""])
        if citations:
            lines.extend(["## 引用", ""])
            lines.extend(f"{index}. `{chunk_id}`" for index, chunk_id in enumerate(citations, start=1))
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    @staticmethod
    def _citation_markers(metadata: dict[str, object], citations: list[str]) -> str:
        values = metadata.get("citations")
        if not isinstance(values, list):
            return ""
        markers: list[str] = []
        for chunk_id in values:
            value = str(chunk_id)
            if value not in citations:
                citations.append(value)
            markers.append(f"[{citations.index(value) + 1}]")
        return " " + "".join(markers) if markers else ""
