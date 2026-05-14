import type { ExportType, MvpContentType } from "./content";
import type { LectureRenderModel } from "./lecture";
import type { PodcastRenderModel } from "./podcast";
import type { SlideRenderModel } from "./slide";
import type { SocialPostRenderModel } from "./socialPost";

export type RenderModel = LectureRenderModel | SlideRenderModel | SocialPostRenderModel | PodcastRenderModel;

export interface ExportFile {
  type: ExportType;
  url: string;
}

export interface TaskProgress {
  stage?: string;
  display_stage?: string;
  current_stage?: string;
  current_node?: string | null;
  current_unit_id?: string | null;
  completed_units?: number;
  total_units?: number;
  percent?: number;
  [key: string]: unknown;
}

export interface TaskResult {
  task_id: string;
  status: "queued" | "running" | "completed" | "failed";
  content_type: MvpContentType;
  preview_url?: string | null;
  export_files: ExportFile[];
  errors: string[];
  current_node?: string | null;
  progress?: TaskProgress;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PreviewResponse {
  content_type: MvpContentType;
  render_model: RenderModel;
}

export interface PartialPreviewResponse extends PreviewResponse {
  is_partial: boolean;
}

export interface TaskStreamEvent {
  event_id: string;
  task_id: string;
  type:
    | "task_started"
    | "outline_ready"
    | "unit_started"
    | "unit_spec_ready"
    | "element_ready"
    | "unit_render_ready"
    | "audio_segment_ready"
    | "direct_spec_ready"
    | "direct_render_ready"
    | "task_completed"
    | "task_failed";
  unit_id?: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface RenderUnitSnapshot {
  unit_id: string;
  order: number;
  content_type: MvpContentType;
  status: "pending" | "rendered" | "failed";
  render_fragment: Record<string, unknown>;
  updated_at?: string | null;
  errors: string[];
}

export interface TaskEventsResponse {
  task_id: string;
  events: TaskStreamEvent[];
}

export interface TaskUnitsResponse {
  task_id: string;
  units: RenderUnitSnapshot[];
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
