import { useContentGenerationStore } from "../../stores/contentGenerationStore";

export function ExportActions() {
  const task = useContentGenerationStore((state) => state.task);
  const exportResult = useContentGenerationStore((state) => state.exportResult);
  const exportTask = useContentGenerationStore((state) => state.exportTask);
  const loading = useContentGenerationStore((state) => state.loading);

  const exportType = task?.content_type === "slide_deck" ? "slide_json" : "pdf";
  const canExport = Boolean(task && task.status === "completed" && !loading);

  return (
    <section className="export-actions">
      <button type="button" disabled={!canExport} onClick={() => exportTask(exportType)}>
        Export {exportType === "pdf" ? "PDF" : "Slide JSON"}
      </button>
      {exportResult ? <a href={exportResult.file_url}>{exportResult.file_url}</a> : null}
    </section>
  );
}
