export type ContentType =
  | "lecture"
  | "slide_deck"
  | "social_post"
  | "podcast_script"
  | "interactive_html"
  | "video_script"
  | "project_task"
  | "quiz_pack"
  | "learning_path";
// TODO(schema-sync): Generate these types from backend JSON Schema/OpenAPI once
// schema automation is added, instead of maintaining frontend mirrors by hand.

export type MvpContentType = "lecture" | "slide_deck" | "social_post" | "podcast_script" | "interactive_html";

export type ElementType =
  | "text"
  | "image"
  | "chart"
  | "mindmap"
  | "table"
  | "quiz"
  | "citation"
  | "audio_script"
  | "audio_file";

export type ExportType = "pdf" | "slide_json" | "image_assets" | "pptx" | "markdown" | "html" | "audio";

export type Difficulty = "introductory" | "intermediate" | "advanced";
export type OutputDepth = "brief" | "standard" | "detailed";
export type CitationPolicy = "none" | "light" | "strict";

export interface GenerationOptions {
  language?: string;
  audience?: string | null;
  difficulty?: Difficulty;
  style?: string;

  duration_minutes?: number | null;
  section_count?: number | null;
  slide_count?: number | null;
  max_section_count?: number;
  max_slide_count?: number;
  output_depth?: OutputDepth;

  include_images?: boolean;
  include_charts?: boolean;
  include_mindmap?: boolean;
  image_style?: string | null;
  citation_policy?: CitationPolicy;

  slide_theme?: string | null;
  speaker_notes?: boolean;
  pdf_options?: Record<string, unknown>;
}

export interface ContentGenerationRequest {
  content_type: MvpContentType;
  topic: string;
  user_prompt: string;
  system_prompt?: string | null;
  knowledge_base_ids?: string[];
  generation_options?: GenerationOptions;
}
