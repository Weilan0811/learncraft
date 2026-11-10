import axios from "axios";
import type {
  AdaptiveBriefResponse,
  CreateSessionResponse,
  SubmitEventRequest,
  SubmitEventResponse,
  SessionStateResponse,
  SessionSummaryResponse,
} from "../types/interactiveHtml";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
});

export async function createLearningSession(lessonId: string): Promise<CreateSessionResponse> {
  const { data } = await api.post<CreateSessionResponse>(
    `/api/interactive-lessons/${lessonId}/sessions`
  );
  return data;
}

export async function submitLearningEvent(
  lessonId: string,
  sessionId: string,
  event: SubmitEventRequest
): Promise<SubmitEventResponse> {
  const { data } = await api.post<SubmitEventResponse>(
    `/api/interactive-lessons/${lessonId}/sessions/${sessionId}/events`,
    event
  );
  return data;
}

export async function getSessionState(
  lessonId: string,
  sessionId: string
): Promise<SessionStateResponse> {
  const { data } = await api.get<SessionStateResponse>(
    `/api/interactive-lessons/${lessonId}/sessions/${sessionId}/state`
  );
  return data;
}

export async function getSessionSummary(
  lessonId: string,
  sessionId: string
): Promise<SessionSummaryResponse> {
  const { data } = await api.get<SessionSummaryResponse>(
    `/api/interactive-lessons/${lessonId}/sessions/${sessionId}/summary`
  );
  return data;
}

export async function createAdaptiveBrief(
  lessonId: string,
  sessionId: string,
  payload: { difficulty?: "introductory" | "intermediate" | "advanced" | null } = {}
): Promise<AdaptiveBriefResponse> {
  const { data } = await api.post<AdaptiveBriefResponse>(
    `/api/interactive-lessons/${lessonId}/sessions/${sessionId}/adaptive-brief`,
    payload
  );
  return data;
}
