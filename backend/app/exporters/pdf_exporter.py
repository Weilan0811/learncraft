from app.schemas.export import ExportRequest, ExportResult
from app.schemas.render import RenderModel
from app.services.storage_service import LocalStorageService, StorageService


class PDFExporter:
    export_type = "pdf"

    def __init__(self, storage_service: StorageService | None = None) -> None:
        self.storage_service = storage_service or LocalStorageService()

    def export(
        self,
        task_id: str,
        render_model: RenderModel,
        request: ExportRequest,
        asset_ids: list[str] | None = None,
    ) -> ExportResult:
        content = self._minimal_pdf(title=getattr(render_model, "title", task_id))
        asset_id = f"export_{task_id}_pdf"
        record = self.storage_service.save_bytes(
            asset_id=asset_id,
            filename=f"{task_id}.pdf",
            content=content,
            content_type="application/pdf",
            kind="pdf",
            metadata={"task_id": task_id, "render_type": getattr(render_model, "render_type", None)},
        )
        return ExportResult(
            export_type=request.export_type,
            file_url=record.url,
            status="success",
            metadata={"asset_id": record.asset_id, "render_type": getattr(render_model, "render_type", None)},
        )

    @staticmethod
    def _minimal_pdf(title: str) -> bytes:
        safe_title = title.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 24 Tf 72 760 Td ({safe_title}) Tj 0 -36 Td (Generated PDF export placeholder.) Tj ET"
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            f"<< /Length {len(stream.encode('latin-1', errors='replace'))} >>\nstream\n{stream}\nendstream".encode(
                "latin-1",
                errors="replace",
            ),
        ]
        chunks = [b"%PDF-1.4\n"]
        offsets: list[int] = []
        for index, obj in enumerate(objects, start=1):
            offsets.append(sum(len(chunk) for chunk in chunks))
            chunks.append(f"{index} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
        xref_offset = sum(len(chunk) for chunk in chunks)
        xref = [b"xref\n", f"0 {len(objects) + 1}\n".encode("ascii"), b"0000000000 65535 f \n"]
        xref.extend(f"{offset:010d} 00000 n \n".encode("ascii") for offset in offsets)
        chunks.extend(
            [
                *xref,
                b"trailer\n",
                f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("ascii"),
                b"startxref\n",
                f"{xref_offset}\n".encode("ascii"),
                b"%%EOF\n",
            ]
        )
        return b"".join(chunks)
