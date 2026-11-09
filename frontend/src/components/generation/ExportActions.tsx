import { useState } from "react";

import { useContentGenerationStore } from "../../stores/contentGenerationStore";
import type { ExportType, MvpContentType } from "../../types/content";
import { LineIcon } from "./icons";

interface ExportOption {
  type: ExportType;
  label: string;
  description: string;
}

const exportOptions: Record<MvpContentType, ExportOption[]> = {
  lecture: [
    { type: "pdf", label: "PDF", description: "排版后的中文讲义" },
    { type: "markdown", label: "Markdown", description: "可继续编辑的文稿" },
    { type: "html", label: "HTML", description: "包含内嵌图片的网页" },
    { type: "image_assets", label: "图片", description: "ZIP 打包全部配图" }
  ],
  slide_deck: [
    { type: "slide_json", label: "Slide JSON", description: "结构化幻灯片数据" },
    { type: "image_assets", label: "图片", description: "幻灯片配图 ZIP" }
  ],
  social_post: [
    { type: "html", label: "HTML", description: "公众号排版预览" },
    { type: "image_assets", label: "图片", description: "封面与配图 ZIP" }
  ],
  podcast_script: [
    { type: "markdown", label: "文稿", description: "双人对话文本" },
    { type: "audio", label: "音频", description: "合成后的完整音频" }
  ],
  interactive_html: [{ type: "html", label: "HTML", description: "包含互动记录的学习讲义" }]
};

const exportLabels: Record<ExportType, string> = {
  pdf: "PDF",
  slide_json: "Slide JSON",
  image_assets: "图片资源包",
  pptx: "PPTX",
  markdown: "Markdown",
  html: "HTML",
  audio: "音频"
};

export function ExportActions() {
  const task = useContentGenerationStore((state) => state.task);
  const exportResult = useContentGenerationStore((state) => state.exportResult);
  const exportTask = useContentGenerationStore((state) => state.exportTask);
  const loading = useContentGenerationStore((state) => state.loading);
  const interactiveSessionId = useContentGenerationStore((state) => state.interactiveSessionId);
  const [pendingType, setPendingType] = useState<ExportType>();

  if (!task || task.status !== "completed") {
    return null;
  }

  if (task.content_type === "interactive_html" && !interactiveSessionId) {
    return <span className="export-hint">完成学习会话后可导出</span>;
  }

  const options = exportOptions[task.content_type] ?? [];

  async function handleExport(type: ExportType) {
    setPendingType(type);
    await exportTask(type);
    setPendingType(undefined);
  }

  return (
    <div className="export-toolbar">
      {options.map((option) => (
        <button
          type="button"
          className="toolbar-button"
          title={option.description}
          disabled={loading || Boolean(pendingType)}
          onClick={() => void handleExport(option.type)}
          key={option.type}
        >
          <LineIcon name="download" size={14} />
          {pendingType === option.type ? "导出中…" : option.label}
        </button>
      ))}
      {exportResult?.status === "failed" ? (
        <span className="export-inline-error">
          导出失败：{String(exportResult.metadata.error ?? "服务端未返回原因")}
        </span>
      ) : null}
      {exportResult?.status === "success" && exportResult.file_url ? (
        <a className="export-inline-success" href={exportResult.file_url} target="_blank" rel="noreferrer">
          已导出，下载
        </a>
      ) : null}
      {task.export_files.length > 0 ? (
        <details className="export-history-inline">
          <summary>已导出 {task.export_files.length}</summary>
          <div>
            {task.export_files.map((file) => (
              <a key={`${file.type}-${file.url}`} href={file.url} target="_blank" rel="noreferrer">
                {exportLabels[file.type] ?? file.type}
              </a>
            ))}
          </div>
        </details>
      ) : null}
    </div>
  );
}
