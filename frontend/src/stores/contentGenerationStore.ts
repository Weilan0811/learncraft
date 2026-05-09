import { create } from "zustand";

import {
  createContentGenerationTask,
  exportContentGenerationTask,
  getContentGenerationPreview,
  getContentGenerationTask
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

const POLL_INTERVAL_MS = 1200;

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function waitForCompletedTask(
  taskId: string,
  onProgress?: (task: TaskResult) => void
): Promise<TaskResult> {
  let task = await getContentGenerationTask(taskId);
  onProgress?.(task);

  while (true) {
    if (task.status === "completed" || task.status === "failed") {
      return task;
    }
    await sleep(POLL_INTERVAL_MS);
    task = await getContentGenerationTask(taskId);
    onProgress?.(task);
  }
}

export const useContentGenerationStore = create<ContentGenerationState>((set, get) => ({
  loading: false,
  async submitTask(request) {
    set({ loading: true, error: undefined, preview: undefined, exportResult: undefined });
    try {
      const createdTask = await createContentGenerationTask(request);
      set({ task: createdTask });

      const completedTask = await waitForCompletedTask(createdTask.task_id, (task) => {
        set({ task });
      });
      set({ task: completedTask });

      if (completedTask.status === "failed") {
        throw new Error(completedTask.errors.join("；") || "内容生成任务执行失败。");
      }

      const preview = await getContentGenerationPreview(completedTask.task_id);
      set({ preview, loading: false });
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
