// Interactive HTML render types.
// The active interactive_html path renders sanitized section HTML fragments
// with per-unit CSS scoping via style_scope_id + css_fragment.

// --- Rendered Unit (matches backend InteractiveHtmlRenderedUnit) ---

export interface InteractiveHtmlRenderBlockRef {
  block_id: string;
  type: string;
  title: string;
  teaching_role: string;
  interaction_ids: string[];
}

export interface InteractionRenderRef {
  interaction_id: string;
  section_id: string;
  type: string;
  target_concepts: string[];
  event_type: string;
}

export interface InteractiveHtmlRenderedUnit {
  section_id: string;
  title: string;
  learning_goal: string;
  style_scope_id: string;
  html_fragment: string;
  css_fragment: string;
  block_manifest: InteractiveHtmlRenderBlockRef[];
  interaction_manifest: InteractionRenderRef[];
  render_notes: Record<string, unknown>;
}

// --- Navigation & Runtime ---

export interface InteractiveHtmlNavigationItem {
  section_id: string;
  title: string;
  anchor: string;
}

export interface InteractiveHtmlRuntimeConfig {
  progress_tracking: boolean;
  scoring_enabled: boolean;
  session_required: boolean;
  event_endpoint_template?: string | null;
}

// --- Top-level Render Model (matches backend InteractiveHtmlRenderModel) ---

export interface InteractiveHtmlRenderModel {
  render_type: "interactive_html_page";
  lesson_id: string;
  title: string;
  subtitle?: string | null;
  layout: "vertical_lesson_with_tutor";
  theme: Record<string, unknown>;
  navigation: InteractiveHtmlNavigationItem[];
  interactions: InteractionRenderRef[];
  runtime: InteractiveHtmlRuntimeConfig;
  meta: Record<string, unknown>;
  pedagogy: Record<string, unknown>;
  sections: InteractiveHtmlRenderedUnit[];
  style_guide: Record<string, unknown>;
  citations: Record<string, unknown>[];
}

// --- Legacy block types (kept for backward compatibility, not used in active render path) ---

export interface InteractiveHtmlRenderBlock {
  block_id: string;
  type: string;
  title?: string | null;
  block_data: Record<string, unknown>;
  metadata: Record<string, unknown>;
  tutor_message?: string | null;
}

export interface InteractiveHtmlRenderSection {
  section_id: string;
  title: string;
  learning_goal: string;
  html_fragment: string;
  block_refs: InteractiveHtmlRenderBlockRef[];
}

export interface InteractiveHtmlBlockRef {
  block_id: string;
  type: string;
  title: string;
  teaching_role: string;
  interaction_ids: string[];
}

export interface InteractiveHtmlInteractionRef {
  interaction_id: string;
  section_id: string;
  type: string;
  target_concepts: string[];
  event_type: LearningEventType;
}

// --- Learning API types ---

export interface CreateSessionResponse {
  session_id: string;
  lesson_id: string;
  state: Record<string, unknown>;
}

export interface LearningEventPayload {
  selected_option_ids?: string[];
  correct_option_ids?: string[];
  ordered_item_ids?: string[];
  match_pairs?: Record<string, string>;
  answer_text?: string | null;
  is_correct?: boolean | null;
  reference_points?: string[];
  matched_points?: string[];
  heuristic_score?: number | null;
  client_timestamp?: string | null;
  confidence?: "low" | "medium" | "high" | null;
  time_spent_seconds?: number | null;
}

export type LearningEventType =
  | "single_choice_answered"
  | "multiple_choice_answered"
  | "short_answer_submitted"
  | "scenario_discussion_submitted"
  | "drag_match_submitted"
  | "sequence_submitted"
  | "socratic_round_answered"
  | "scenario_choice_selected"
  | "hint_requested"
  | "confused_clicked";

export interface SubmitEventRequest {
  section_id: string;
  block_id?: string | null;
  interaction_id?: string | null;
  event_type: LearningEventType;
  payload: LearningEventPayload;
}

export interface EventFeedback {
  message: string;
  tone: "encouraging" | "corrective" | "socratic";
}

export interface SubmitEventResponse {
  event_id: string;
  feedback: EventFeedback;
  event_saved: boolean;
}

export interface SessionStateResponse {
  session_id: string;
  lesson_id: string;
  total_events: number;
  interaction_summary: Record<string, unknown>;
}
