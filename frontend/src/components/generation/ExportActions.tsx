import { useContentGenerationStore } from "../../stores/contentGenerationStore";

export function ExportActions() {
  // TODO(MVP-export): Support multiple export formats, disabled reasons,
  // download progress, failed export retries, and generated file metadata.
  const task = useContentGenerationStore((state) => state.task);
  const exportResult = useContentGenerationStore((state) => state.exportResult);
  const exportTask = useContentGenerationStore((state) => state.exportTask);
  const loading = useContentGenerationStore((state) => state.loading);

  const exportType = task?.content_type === "slide_deck" ? "slide_json" : "pdf";

  return (
    <section className="export-actions">
      <button type="button" disabled={!task || loading} onClick={() => exportTask(exportType)}>
        导出 {exportType === "pdf" ? "PDF" : "Slide JSON"}
      </button>
      {exportResult ? <a href={exportResult.file_url}>{exportResult.file_url}</a> : null}
    </section>
  );
}
