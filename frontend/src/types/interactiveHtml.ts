// Interactive HTML Block types — mirrors backend LessonBlock discriminated union.

// --- Base ---

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
  render_blocks: InteractiveHtmlRenderBlock[];
}

export interface InteractiveHtmlRenderModel {
  render_type: "interactive_html_page";
  lesson_id: string;
  title: string;
  subtitle?: string | null;
  meta: Record<string, unknown>;
  pedagogy: Record<string, unknown>;
  sections: InteractiveHtmlRenderSection[];
  citations: Record<string, unknown>[];
}

// --- Learning API types ---

export interface CreateSessionResponse {
  session_id: string;
  lesson_id: string;
  state: Record<string, unknown>;
}

export interface LearningEventPayload {
  selected_option_ids?: string[];
  ordered_item_ids?: string[];
  match_pairs?: Record<string, string>;
  answer_text?: string | null;
  confidence?: "low" | "medium" | "high" | null;
  time_spent_seconds?: number | null;
}

export type LearningEventType =
  | "single_choice_answered"
  | "multiple_choice_answered"
  | "short_answer_submitted"
  | "drag_match_submitted"
  | "sequence_submitted"
  | "socratic_round_answered"
  | "scenario_choice_selected"
  | "hint_requested"
  | "confused_clicked";

export interface SubmitEventRequest {
  section_id: string;
  block_id: string;
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
