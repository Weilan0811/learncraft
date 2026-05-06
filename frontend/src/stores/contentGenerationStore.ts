import { create } from "zustand";

import {
  createContentGenerationTask,
  exportContentGenerationTask,
  getContentGenerationPreview
} from "../api/contentGenerationApi";
import type { ContentGenerationRequest } from "../types/content";
import type { ExportResult, PreviewResponse, TaskResult } from "../types/export";

interface ContentGenerationState {
  task?: TaskResult;
  preview?: PreviewResponse;
  exportResult?: ExportResult;
  loading: boolean;
  error?: string;
  submitTask: (request: ContentGenerationRequest) => Promise<void>;
  exportTask: (exportType: "pdf" | "slide_json") => Promise<void>;
}

export const useContentGenerationStore = create<ContentGenerationState>((set, get) => ({
  loading: false,
  async submitTask(request) {
    set({ loading: true, error: undefined });
    try {
      const task = await createContentGenerationTask(request);
      const preview = await getContentGenerationPreview(task.task_id);
      set({ task, preview, loading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Unknown request error", loading: false });
    }
  },
  async exportTask(exportType) {
    const taskId = get().task?.task_id;
    if (!taskId) {
      set({ error: "No task is available to export." });
      return;
    }
    set({ loading: true, error: undefined });
    try {
      const exportResult = await exportContentGenerationTask(taskId, { export_type: exportType });
      set({ exportResult, loading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Unknown export error", loading: false });
    }
  }
}));
