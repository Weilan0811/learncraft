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
const MAX_POLL_TIMES = 120;

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function waitForCompletedTask(taskId: string): Promise<TaskResult> {
  let task = await getContentGenerationTask(taskId);

  for (let i = 0; i < MAX_POLL_TIMES; i += 1) {
    if (task.status === "completed" || task.status === "failed") {
      return task;
    }
    await sleep(POLL_INTERVAL_MS);
    task = await getContentGenerationTask(taskId);
  }

  throw new Error("任务执行超时，请稍后在任务历史中重新查看。送达后端的请求已创建成功。");
}

export const useContentGenerationStore = create<ContentGenerationState>((set, get) => ({
  loading: false,
  async submitTask(request) {
    set({ loading: true, error: undefined, preview: undefined, exportResult: undefined });
    try {
      const createdTask = await createContentGenerationTask(request);
      set({ task: createdTask });

      const completedTask = await waitForCompletedTask(createdTask.task_id);
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
