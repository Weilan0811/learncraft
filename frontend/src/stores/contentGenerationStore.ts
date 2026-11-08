import { create } from "zustand";

import {
  createContentGenerationTask,
  exportContentGenerationTask,
  getContentGenerationEvents,
  getContentGenerationPartialPreview,
  getContentGenerationPreview,
  getContentGenerationTask,
  getContentGenerationUnits,
  subscribeContentGenerationStream
} from "../api/contentGenerationApi";
import type { ContentGenerationRequest, ExportType } from "../types/content";
import type {
  ExportResult,
  PartialPreviewResponse,
  PreviewResponse,
  RenderUnitSnapshot,
  TaskResult,
  TaskStreamEvent
} from "../types/export";

interface ContentGenerationState {
  task?: TaskResult;
  preview?: PreviewResponse;
  partialPreview?: PartialPreviewResponse;
  streamEvents: TaskStreamEvent[];
  renderUnits: RenderUnitSnapshot[];
  exportResult?: ExportResult;
  interactiveSessionId?: string;
  loading: boolean;
  previewLookupLoading: boolean;
  error?: string;
  submitTask: (request: ContentGenerationRequest) => Promise<void>;
  loadPreviewByTaskId: (taskId: string) => Promise<void>;
  exportTask: (exportType: ExportType) => Promise<void>;
  setInteractiveSessionId: (sessionId?: string) => void;
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

interface SseWaitHandlers {
  onTaskPatch: (patch: Partial<TaskResult>) => void;
  onRefresh: () => void;
  onPollFallback: () => Promise<TaskResult>;
}

/**
 * Wait for task completion over the backend SSE stream. Snapshots are
 * lightweight, so unit/event refreshes are triggered only when the counters
 * change — this removes the 1-2 beat lag of interval polling. Any SSE error
 * (including the backend closing the stream before a terminal frame) falls
 * back to interval polling exactly once.
 */
async function waitForCompletedTaskSse(taskId: string, handlers: SseWaitHandlers): Promise<TaskResult> {
  return new Promise<TaskResult>((resolve, reject) => {
    let settled = false;
    let lastUnitsCount = -1;
    let lastEventsCount = -1;
    let unsubscribe: (() => void) | undefined;

    const finish = (taskPromise: Promise<TaskResult>) => {
      settled = true;
      unsubscribe?.();
      taskPromise.then(resolve, reject);
    };

    unsubscribe = subscribeContentGenerationStream(
      taskId,
      (snapshot) => {
        if (settled) {
          return;
        }
        const patch: Partial<TaskResult> = {};
        if (snapshot.status) {
          patch.status = snapshot.status as TaskResult["status"];
        }
        if (snapshot.progress) {
          patch.progress = snapshot.progress as TaskResult["progress"];
        }
        if (snapshot.current_node != null) {
          patch.current_node = snapshot.current_node;
        }
        if (snapshot.errors && snapshot.errors.length > 0) {
          patch.errors = snapshot.errors;
        }
        handlers.onTaskPatch(patch);

        if (snapshot.units_count !== lastUnitsCount || snapshot.events_count !== lastEventsCount) {
          lastUnitsCount = snapshot.units_count ?? -1;
          lastEventsCount = snapshot.events_count ?? -1;
          handlers.onRefresh();
        }
        if (snapshot.done || snapshot.missing) {
          finish(getContentGenerationTask(taskId));
        }
      },
      () => {
        if (settled) {
          return;
        }
        finish(handlers.onPollFallback());
      }
    );
  });
}

export const useContentGenerationStore = create<ContentGenerationState>((set, get) => ({
  streamEvents: [],
  renderUnits: [],
  interactiveSessionId: undefined,
  loading: false,
  previewLookupLoading: false,
  setInteractiveSessionId(sessionId) {
    set({ interactiveSessionId: sessionId });
  },
  async submitTask(request) {
    set({
      loading: true,
      error: undefined,
      preview: undefined,
      partialPreview: undefined,
      streamEvents: [],
      renderUnits: [],
      interactiveSessionId: undefined,
      exportResult: undefined
    });
    try {
      const createdTask = await createContentGenerationTask(request);
      set({ task: createdTask });

      let refreshVersion = 0;
      let lastAppliedRefresh = 0;
      const refreshStreamingState = async (taskId: string) => {
        const version = ++refreshVersion;
        const [eventsResult, unitsResult, partialPreview] = await Promise.allSettled([
          getContentGenerationEvents(taskId),
          getContentGenerationUnits(taskId),
          getContentGenerationPartialPreview(taskId)
        ]);
        if (version < lastAppliedRefresh || get().task?.task_id !== taskId) {
          return;
        }
        lastAppliedRefresh = version;
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

      const completedTask = await waitForCompletedTaskSse(createdTask.task_id, {
        onTaskPatch: (patch) => {
          const current = get().task;
          if (current && current.task_id === createdTask.task_id) {
            set({ task: { ...current, ...patch } });
          }
        },
        onRefresh: () => {
          void refreshStreamingState(createdTask.task_id);
        },
        onPollFallback: async () => {
          const polled = await waitForCompletedTask(createdTask.task_id, async (task) => {
            set({ task });
            await refreshStreamingState(task.task_id);
          });
          set({ task: polled });
          return polled;
        }
      });
      set({ task: completedTask });

      if (completedTask.status === "failed") {
        throw new Error(completedTask.errors.join("; ") || "内容生成任务执行失败。");
      }

      const preview = await getContentGenerationPreview(completedTask.task_id);
      await refreshStreamingState(completedTask.task_id);
      set({ preview, loading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Unknown request error", loading: false });
    }
  },

  async loadPreviewByTaskId(taskId) {
    const normalizedTaskId = taskId.trim();
    if (!normalizedTaskId) {
      set({ error: "请输入 task_id 后再查询预览。" });
      return;
    }

    set({
      previewLookupLoading: true,
      error: undefined,
      task: undefined,
      preview: undefined,
      partialPreview: undefined,
      streamEvents: [],
      renderUnits: [],
      interactiveSessionId: undefined,
      exportResult: undefined
    });

    try {
      const task = await getContentGenerationTask(normalizedTaskId);
      const [eventsResult, unitsResult, previewResult] = await Promise.allSettled([
        getContentGenerationEvents(normalizedTaskId),
        getContentGenerationUnits(normalizedTaskId),
        getContentGenerationPreview(normalizedTaskId)
      ]);

      if (previewResult.status === "fulfilled") {
        set({ preview: previewResult.value, partialPreview: undefined });
      } else {
        const partialPreview = await getContentGenerationPartialPreview(normalizedTaskId);
        set({ preview: undefined, partialPreview });
      }

      set({
        task,
        streamEvents: eventsResult.status === "fulfilled" ? eventsResult.value.events : [],
        renderUnits: unitsResult.status === "fulfilled" ? unitsResult.value.units : [],
        previewLookupLoading: false
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Unknown preview lookup error",
        previewLookupLoading: false
      });
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
      const task = get().task;
      const interactiveSessionId = get().interactiveSessionId;
      const exportResult = await exportContentGenerationTask(taskId, {
        export_type: exportType,
        export_options:
          task?.content_type === "interactive_html" && exportType === "html" && interactiveSessionId
            ? { session_id: interactiveSessionId }
            : undefined
      });
      set({ exportResult, loading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Unknown export error", loading: false });
    }
  }
}));
