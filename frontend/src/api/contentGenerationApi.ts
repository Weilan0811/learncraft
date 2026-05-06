import axios from "axios";

import type { ContentGenerationRequest } from "../types/content";
import type { ExportRequest, ExportResult, PreviewResponse, TaskResult } from "../types/export";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? ""
});
// TODO(MVP-api): Add auth headers, unified error normalization, request
// tracing, task polling helpers, and cancellation/retry endpoints.

export async function createContentGenerationTask(request: ContentGenerationRequest): Promise<TaskResult> {
  const { data } = await api.post<TaskResult>("/api/content-generation/tasks", request);
  return data;
}

export async function getContentGenerationTask(taskId: string): Promise<TaskResult> {
  const { data } = await api.get<TaskResult>(`/api/content-generation/tasks/${taskId}`);
  return data;
}

export async function getContentGenerationPreview(taskId: string): Promise<PreviewResponse> {
  const { data } = await api.get<PreviewResponse>(`/api/content-generation/tasks/${taskId}/preview`);
  return data;
}

export async function exportContentGenerationTask(taskId: string, request: ExportRequest): Promise<ExportResult> {
  const { data } = await api.post<ExportResult>(`/api/content-generation/tasks/${taskId}/export`, request);
  return data;
}
