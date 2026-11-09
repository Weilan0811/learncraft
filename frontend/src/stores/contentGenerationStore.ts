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
  TaskEventsResponse,
  TaskResult,
  TaskStreamEvent,
  TaskUnitsResponse
} from "../types/export";

interface ContentGenerationState {
  task?: TaskResult;
  preview?: PreviewResponse;
  partialPreview?: PartialPreviewResponse;
  streamEvents: TaskStreamEvent[];
  renderUnits: RenderUnitSnapshot[];
  exportResult?: ExportResult;
  interactiveSessionId?: string;
  lastRequest?: ContentGenerationRequest;
  loading: boolean;
  previewLookupLoading: boolean;
  error?: string;
  streamRefreshError?: string;
  submitTask: (request: ContentGenerationRequest) => Promise<void>;
  retryLastTask: () => Promise<void>;
  loadPreviewByTaskId: (taskId: string) => Promise<void>;
  exportTask: (exportType: ExportType) => Promise<void>;
  setInteractiveSessionId: (sessionId?: string) => void;
  retryStreamRefresh: () => void;
  stopStreamRefresh: () => void;
}

const POLL_INTERVAL_MS = 1200;
const MAX_STREAM_REFRESH_RETRIES = 3;

type StreamPart = "events" | "units" | "preview";
let activeStreamRefresh: { retryFailed: () => void; dispose: () => void } | undefined;

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
    if (task.status === "completed" || task.status === "failed" || task.status === "interrupted") {
      return task;
    }
    await sleep(POLL_INTERVAL_MS);
    task = await getContentGenerationTask(taskId);
    await onProgress?.(task);
  }
}

interface SseWaitHandlers {
  onTaskPatch: (patch: Partial<TaskResult>) => void;
  onRefresh: (unitsCount: number) => void;
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
          handlers.onRefresh(snapshot.units_count ?? 0);
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
  retryStreamRefresh() {
    activeStreamRefresh?.retryFailed();
  },
  stopStreamRefresh() {
    activeStreamRefresh?.dispose();
    activeStreamRefresh = undefined;
    set({ streamRefreshError: undefined });
  },
  setInteractiveSessionId(sessionId) {
    set({ interactiveSessionId: sessionId });
  },
  async submitTask(request) {
    get().stopStreamRefresh();
    set({
      loading: true,
      error: undefined,
      streamRefreshError: undefined,
      task: undefined,
      lastRequest: request,
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

      let disposed = false;
      let previewExpected = false;
      let previewDisabled = false;
      const latestRequested = { events: 0, units: 0, preview: 0 };
      const lastAppliedRefresh = { events: 0, units: 0, preview: 0 };
      const retryTimers: Partial<Record<StreamPart, number>> = {};
      const failedParts = new Set<StreamPart>();
      const isCurrent = () => !disposed && get().task?.task_id === createdTask.task_id;
      const updateRefreshError = () => {
        if (isCurrent()) {
          set({ streamRefreshError: failedParts.size ? "部分进度或预览暂时无法更新。" : undefined });
        }
      };

      const requestParts = (parts: StreamPart[]): Promise<void> => Promise.all(parts.map((part) => {
        if (!isCurrent() || (part === "preview" && previewDisabled)) return Promise.resolve();
        window.clearTimeout(retryTimers[part]);
        const version = ++latestRequested[part];
        return fetchPart(part, version, 0);
      })).then(() => undefined);

      const fetchPart = async (part: StreamPart, version: number, attempt: number): Promise<void> => {
        if (!isCurrent() || version !== latestRequested[part] || (part === "preview" && previewDisabled)) return;
        try {
          const result = part === "events"
            ? await getContentGenerationEvents(createdTask.task_id)
            : part === "units"
              ? await getContentGenerationUnits(createdTask.task_id)
              : await getContentGenerationPartialPreview(createdTask.task_id);
          if (!isCurrent() || (part === "preview" && previewDisabled) || version <= lastAppliedRefresh[part]) return;
          lastAppliedRefresh[part] = version;
          if (version === latestRequested[part]) {
            failedParts.delete(part);
            updateRefreshError();
          }
          if (part === "events") {
            set({ streamEvents: (result as TaskEventsResponse).events });
          } else if (part === "units") {
            const units = (result as TaskUnitsResponse).units;
            set({ renderUnits: units });
            if (units.length > 0 && !previewExpected && !previewDisabled) {
              previewExpected = true;
              void requestParts(["preview"]);
            }
          } else {
            set({ partialPreview: result as PartialPreviewResponse });
          }
        } catch {
          if (!isCurrent() || version !== latestRequested[part] || (part === "preview" && previewDisabled)) return;
          if (attempt < MAX_STREAM_REFRESH_RETRIES) {
            retryTimers[part] = window.setTimeout(() => {
              delete retryTimers[part];
              void fetchPart(part, version, attempt + 1);
            }, POLL_INTERVAL_MS);
          } else {
            failedParts.add(part);
            updateRefreshError();
          }
        }
      };

      activeStreamRefresh = {
        retryFailed: () => { void requestParts([...failedParts]); },
        dispose: () => {
          disposed = true;
          for (const timer of Object.values(retryTimers)) window.clearTimeout(timer);
        }
      };

      const refreshStreamingState = (unitsCount: number) => {
        previewExpected ||= unitsCount > 0;
        return requestParts(previewExpected && !previewDisabled ? ["events", "units", "preview"] : ["events", "units"]);
      };

      const completedTask = await waitForCompletedTaskSse(createdTask.task_id, {
        onTaskPatch: (patch) => {
          const current = get().task;
          if (current && current.task_id === createdTask.task_id) {
            set({ task: { ...current, ...patch } });
          }
        },
        onRefresh: (unitsCount) => {
          void refreshStreamingState(unitsCount);
        },
        onPollFallback: async () => {
          const polled = await waitForCompletedTask(createdTask.task_id, async (task) => {
            set({ task });
            await refreshStreamingState(task.progress?.completed_units ?? 0);
          });
          set({ task: polled });
          return polled;
        }
      });
      set({ task: completedTask });

      if (completedTask.status === "failed") {
        throw new Error(completedTask.errors.join("; ") || "内容生成任务执行失败。");
      }

      if (completedTask.status === "interrupted") {
        throw new Error(completedTask.progress?.interrupted_reason || "任务已中断，请重新生成。");
      }

      const preview = await getContentGenerationPreview(completedTask.task_id);
      previewDisabled = true;
      window.clearTimeout(retryTimers.preview);
      failedParts.delete("preview");
      updateRefreshError();
      await refreshStreamingState(0);
      set({ preview, loading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Unknown request error", loading: false });
    }
  },

  async retryLastTask() {
    const lastRequest = get().lastRequest;
    if (!lastRequest) {
      set({ error: "没有可重试的生成参数，请重新填写表单。" });
      return;
    }
    await get().submitTask(lastRequest);
  },

  async loadPreviewByTaskId(taskId) {
    const normalizedTaskId = taskId.trim();
    if (!normalizedTaskId) {
      set({ error: "请输入 task_id 后再查询预览。" });
      return;
    }

    get().stopStreamRefresh();
    set({
      previewLookupLoading: true,
      error: undefined,
      streamRefreshError: undefined,
      task: undefined,
      lastRequest: undefined,
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
