import type { ExportType, MvpContentType } from "./content";
import type { LectureRenderModel } from "./lecture";
import type { SlideRenderModel } from "./slide";

export type RenderModel = LectureRenderModel | SlideRenderModel;

export interface ExportFile {
  type: ExportType;
  url: string;
}

export interface TaskResult {
  task_id: string;
  status: "queued" | "running" | "completed" | "failed";
  content_type: MvpContentType;
  preview_url?: string | null;
  export_files: ExportFile[];
  errors: string[];
  // TODO(MVP-task): Add progress, current_node, timestamps, and structured
  // error details after backend task state is persisted.
}

export interface PreviewResponse {
  content_type: MvpContentType;
  render_model: RenderModel;
}

export interface ExportRequest {
  export_type: ExportType;
  export_options?: Record<string, unknown>;
}

export interface ExportResult {
  export_type: ExportType;
  file_url: string;
  status: "success" | "failed";
  metadata: Record<string, unknown>;
}
