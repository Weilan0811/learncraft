import { useContentGenerationStore } from "../../stores/contentGenerationStore";
import type { ExportResult } from "../../types/export";
import type { ExportType, MvpContentType } from "../../types/content";

function defaultExportType(contentType?: MvpContentType): ExportType {
  if (contentType === "slide_deck") {
    return "slide_json";
  }

  if (contentType === "social_post") {
    return "html";
  }

  if (contentType === "podcast_script") {
    return "markdown";
  }

  return "pdf";
}

function exportLabel(exportType: ExportType) {
  if (exportType === "slide_json") {
    return "Slide JSON";
  }

  if (exportType === "html") {
    return "HTML";
  }

  if (exportType === "image_assets") {
    return "Image Assets";
  }

  if (exportType === "markdown") {
    return "Markdown";
  }

  if (exportType === "audio") {
    return "Audio";
  }

  return "PDF";
}

function articleJsonUrl(result?: ExportResult | null) {
  const assetId = result?.metadata?.article_json_asset_id;
  return typeof assetId === "string" ? `/api/assets/${assetId}/download` : undefined;
}

export function ExportActions() {
  const task = useContentGenerationStore((state) => state.task);
  const exportResult = useContentGenerationStore((state) => state.exportResult);
  const exportTask = useContentGenerationStore((state) => state.exportTask);
  const loading = useContentGenerationStore((state) => state.loading);

  const exportType = defaultExportType(task?.content_type);
  const exportName = exportLabel(exportType);
  const canExport = Boolean(task && task.status === "completed" && !loading);
  const jsonUrl = articleJsonUrl(exportResult);
  const podcastExportTypes: ExportType[] = ["markdown", "audio"];

  return (
    <section className="export-actions">
      {task?.content_type === "podcast_script" ? (
        podcastExportTypes.map((type) => (
          <button type="button" disabled={!canExport} onClick={() => exportTask(type)} key={type}>
            Export {exportLabel(type)}
          </button>
        ))
      ) : (
        <button type="button" disabled={!canExport} onClick={() => exportTask(exportType)}>
          Export {exportName}
        </button>
      )}
      {exportResult?.status === "failed" ? (
        <p className="error-text">Export failed: {String(exportResult.metadata?.error ?? "unsupported")}</p>
      ) : null}
      {exportResult?.status === "success" && exportResult.file_url ? (
        <a href={exportResult.file_url}>Download {exportLabel(exportResult.export_type)}</a>
      ) : null}
      {jsonUrl ? <a href={jsonUrl}>Download Article JSON</a> : null}
    </section>
  );
}
