import { create } from "zustand";

import {
  createContentGenerationTask,
  exportContentGenerationTask,
  getContentGenerationEvents,
  getContentGenerationPartialPreview,
  getContentGenerationPreview,
  getContentGenerationTask,
  getContentGenerationUnits
} from "../api/contentGenerationApi";
import type { ContentGenerationRequest } from "../types/content";
import type { ExportResult, PartialPreviewResponse, PreviewResponse, RenderUnitSnapshot, TaskResult, TaskStreamEvent } from "../types/export";

interface ContentGenerationState {
  task?: TaskResult;
  preview?: PreviewResponse;
  partialPreview?: PartialPreviewResponse;
  streamEvents: TaskStreamEvent[];
  renderUnits: RenderUnitSnapshot[];
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
  onProgress?: (task: TaskResult) => Promise<void> | void
): Promise<TaskResult> {
  let task = await getContentGenerationTask(taskId);
  await onProgress?.(task);

  while (true) {
    if (task.status === "completed" || task.status === "failed") {
      return task;
    }
    await sleep(POLL_INTERVAL_MS);
    task = await getContentGenerationTask(taskId);
    await onProgress?.(task);
  }
}

export const useContentGenerationStore = create<ContentGenerationState>((set, get) => ({
  streamEvents: [],
  renderUnits: [],
  loading: false,
  async submitTask(request) {
    set({ loading: true, error: undefined, preview: undefined, partialPreview: undefined, streamEvents: [], renderUnits: [], exportResult: undefined });
    try {
      const createdTask = await createContentGenerationTask(request);
      set({ task: createdTask });

      const refreshStreamingState = async (taskId: string) => {
        const [eventsResult, unitsResult, partialPreview] = await Promise.allSettled([
          getContentGenerationEvents(taskId),
          getContentGenerationUnits(taskId),
          getContentGenerationPartialPreview(taskId)
        ]);
        if (eventsResult.status === "fulfilled") {
          set({ streamEvents: eventsResult.value.events });
        }
        if (unitsResult.status === "fulfilled") {
          set({ renderUnits: unitsResult.value.units });
        }
        if (partialPreview.status === "fulfilled") {
          set({ partialPreview: partialPreview.value });
        }
      };

      const completedTask = await waitForCompletedTask(createdTask.task_id, async (task) => {
        set({ task });
        await refreshStreamingState(task.task_id);
      });
      set({ task: completedTask });

      if (completedTask.status === "failed") {
        throw new Error(completedTask.errors.join("；") || "内容生成任务执行失败。");
      }

      const preview = await getContentGenerationPreview(completedTask.task_id);
      await refreshStreamingState(completedTask.task_id);
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
