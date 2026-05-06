export type ContentType =
  | "lecture"
  | "slide_deck"
  | "social_post"
  | "podcast_script"
  | "video_script"
  | "project_task"
  | "quiz_pack"
  | "learning_path";

export type MvpContentType = "lecture" | "slide_deck";

export type ElementType =
  | "text"
  | "image"
  | "chart"
  | "mindmap"
  | "table"
  | "quiz"
  | "citation";

export type ExportType = "preview" | "pdf" | "slide_json" | "image_assets" | "pptx" | "markdown" | "html";

export interface GenerationOptions {
  language: string;
  difficulty: string;
  style: string;
  include_images: boolean;
  include_charts: boolean;
  include_mindmap: boolean;
}

export interface ContentGenerationRequest {
  content_type: MvpContentType;
  topic: string;
  user_prompt: string;
  system_prompt?: string | null;
  knowledge_base_ids: string[];
  output_formats: ExportType[];
  generation_options: GenerationOptions;
}
