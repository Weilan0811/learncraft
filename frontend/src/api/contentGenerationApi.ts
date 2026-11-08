import axios, { AxiosError } from "axios";

import type { ContentGenerationRequest } from "../types/content";
import type {
  ExportRequest,
  ExportResult,
  PartialPreviewResponse,
  PreviewResponse,
  TaskEventsResponse,
  TaskResult,
  TaskUnitsResponse
} from "../types/export";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? ""
});
const STREAM_REQUEST_TIMEOUT_MS = 15000;
// TODO(MVP-api): Add auth headers, request tracing, cancellation/retry
// endpoints, and OpenAPI-generated client types.

function getApiErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    return error instanceof Error ? error.message : "Unknown request error";
  }

  const axiosError = error as AxiosError<unknown>;
  const status = axiosError.response?.status;
  const payload = axiosError.response?.data;

  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    return `HTTP ${status}: ${JSON.stringify((payload as { detail: unknown }).detail)}`;
  }

  return `HTTP ${status ?? "unknown"}: ${axiosError.message}`;
}

async function unwrapApiCall<T>(call: Promise<{ data: T }>): Promise<T> {
  try {
    const { data } = await call;
    return data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error));
  }
}

export async function createContentGenerationTask(request: ContentGenerationRequest): Promise<TaskResult> {
  return unwrapApiCall(api.post<TaskResult>("/api/content-generation/tasks", request));
}

export async function getContentGenerationTask(taskId: string): Promise<TaskResult> {
  return unwrapApiCall(api.get<TaskResult>(`/api/content-generation/tasks/${taskId}`));
}

export async function getContentGenerationPreview(taskId: string): Promise<PreviewResponse> {
  return unwrapApiCall(api.get<PreviewResponse>(`/api/content-generation/tasks/${taskId}/preview`));
}

export async function getContentGenerationPartialPreview(taskId: string): Promise<PartialPreviewResponse> {
  return unwrapApiCall(api.get<PartialPreviewResponse>(`/api/content-generation/tasks/${taskId}/preview/partial`, { timeout: STREAM_REQUEST_TIMEOUT_MS }));
}

export async function getContentGenerationEvents(taskId: string): Promise<TaskEventsResponse> {
  return unwrapApiCall(api.get<TaskEventsResponse>(`/api/content-generation/tasks/${taskId}/events`, { timeout: STREAM_REQUEST_TIMEOUT_MS }));
}

export async function getContentGenerationUnits(taskId: string): Promise<TaskUnitsResponse> {
  return unwrapApiCall(api.get<TaskUnitsResponse>(`/api/content-generation/tasks/${taskId}/units`, { timeout: STREAM_REQUEST_TIMEOUT_MS }));
}

export async function exportContentGenerationTask(taskId: string, request: ExportRequest): Promise<ExportResult> {
  return unwrapApiCall(api.post<ExportResult>(`/api/content-generation/tasks/${taskId}/export`, request));
}

export interface TaskStreamSnapshot {
  task_id: string;
  status: string;
  progress?: Record<string, unknown>;
  current_node?: string | null;
  errors?: string[];
  units_count?: number;
  events_count?: number;
  done?: boolean;
  missing?: boolean;
}

/**
 * Subscribe to the backend SSE progress stream for a task. Returns an
 * unsubscribe function that closes the connection. Frames are lightweight
 * (status/progress/counters); heavy payloads should be refetched through
 * the regular endpoints when the counters change.
 */
export function subscribeContentGenerationStream(
  taskId: string,
  onSnapshot: (snapshot: TaskStreamSnapshot) => void,
  onError?: (error: Event) => void
): () => void {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const source = new EventSource(`${base}/api/content-generation/tasks/${taskId}/events/stream`);
  source.onmessage = (event) => {
    try {
      onSnapshot(JSON.parse(event.data) as TaskStreamSnapshot);
    } catch {
      // Ignore malformed frames; the next snapshot will resync.
    }
  };
  if (onError) {
    source.onerror = (event) => onError(event);
  }
  return () => source.close();
}
