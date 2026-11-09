import { create } from "zustand";

import {
  createContentGenerationTask,
  exportContentGenerationTask,
  getContentGenerationEvents,
  getContentGenerationPartialPreview,
  getContentGenerationPreview,
  getContentGenerationTask,
  getContentGenerationUnits,
  getTaskFailedResources,
  retryTaskResource,
  subscribeContentGenerationStream
} from "../api/contentGenerationApi";
import type { ContentGenerationRequest, ExportType } from "../types/content";
import type {
  ExportResult,
  PartialPreviewResponse,
  PreviewResponse,
  RenderUnitSnapshot,
  TaskEventsResponse,
  TaskResource,
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
  failedResources: TaskResource[];
  resourceRetryError?: string;
  resourceUpdated: boolean;
  loading: boolean;
  previewLookupLoading: boolean;
  error?: string;
  streamRefreshError?: string;
  submitTask: (request: ContentGenerationRequest) => Promise<void>;
  retryLastTask: () => Promise<void>;
  loadPreviewByTaskId: (taskId: string) => Promise<void>;
  trackTask: (taskId: string) => void;
  loadFailedResources: () => Promise<void>;
  retryResource: (resourceId: string) => Promise<void>;
  trackResourceRetry: (resourceId: string) => Promise<void>;
  exportTask: (exportType: ExportType) => Promise<void>;
  setInteractiveSessionId: (sessionId?: string) => void;
  retryStreamRefresh: () => void;
  stopStreamRefresh: () => void;
}

const POLL_INTERVAL_MS = 1200;
const MAX_STREAM_REFRESH_RETRIES = 3;

type StreamPart = "events" | "units" | "preview";
let activeStreamRefresh: { retryFailed: () => void; dispose: () => void } | undefined;
let activeResourcePolling: { taskId: string; resourceId: string; dispose: () => void } | undefined;
let taskViewVersion = 0;
let activeGenerationWait: AbortController | undefined;
let failedResourcesRequestId = 0;

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function waitForCompletedTask(
  taskId: string,
  signal: AbortSignal,
  onProgress?: (task: TaskResult) => Promise<void> | void
): Promise<TaskResult> {
  let task = await getContentGenerationTask(taskId);
  signal.throwIfAborted();
  await onProgress?.(task);

  while (true) {
    if (task.status === "completed" || task.status === "failed" || task.status === "interrupted") {
      return task;
    }
    await sleep(POLL_INTERVAL_MS);
    signal.throwIfAborted();
    task = await getContentGenerationTask(taskId);
    signal.throwIfAborted();
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
async function waitForCompletedTaskSse(taskId: string, handlers: SseWaitHandlers, signal: AbortSignal): Promise<TaskResult> {
  signal.throwIfAborted();
  return new Promise<TaskResult>((resolve, reject) => {
    let settled = false;
    let lastUnitsCount = -1;
    let lastEventsCount = -1;
    let unsubscribe: (() => void) | undefined;
    const onAbort = () => {
      settled = true;
      unsubscribe?.();
      reject(signal.reason);
    };
    signal.addEventListener("abort", onAbort, { once: true });

    const finish = (taskPromise: Promise<TaskResult>) => {
      settled = true;
      unsubscribe?.();
      taskPromise.then(resolve, reject).finally(() => signal.removeEventListener("abort", onAbort));
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
  failedResources: [],
  resourceUpdated: false,
  interactiveSessionId: undefined,
  loading: false,
  previewLookupLoading: false,
  retryStreamRefresh() {
    activeStreamRefresh?.retryFailed();
  },
  stopStreamRefresh() {
    taskViewVersion += 1;
    activeGenerationWait?.abort();
    activeGenerationWait = undefined;
    activeStreamRefresh?.dispose();
    activeStreamRefresh = undefined;
    activeResourcePolling?.dispose();
    activeResourcePolling = undefined;
    set({ streamRefreshError: undefined, loading: false, previewLookupLoading: false });
  },
  setInteractiveSessionId(sessionId) {
    set({ interactiveSessionId: sessionId });
  },
  async submitTask(request) {
    get().stopStreamRefresh();
    const viewVersion = taskViewVersion;
    const isActiveView = () => viewVersion === taskViewVersion;
    const generationWait = new AbortController();
    activeGenerationWait = generationWait;
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
      failedResources: [],
      resourceRetryError: undefined,
      resourceUpdated: false,
      interactiveSessionId: undefined,
      exportResult: undefined
    });
    try {
      const createdTask = await createContentGenerationTask(request);
      if (!isActiveView()) return;
      set({ task: createdTask });

      let disposed = false;
      let previewExpected = false;
      let previewDisabled = false;
      const latestRequested = { events: 0, units: 0, preview: 0 };
      const lastAppliedRefresh = { events: 0, units: 0, preview: 0 };
      const retryTimers: Partial<Record<StreamPart, number>> = {};
      const failedParts = new Set<StreamPart>();
      const isCurrent = () => isActiveView() && !disposed && get().task?.task_id === createdTask.task_id;
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
          if (isCurrent() && current) {
            set({ task: { ...current, ...patch } });
          }
        },
        onRefresh: (unitsCount) => {
          void refreshStreamingState(unitsCount);
        },
        onPollFallback: async () => {
          const polled = await waitForCompletedTask(createdTask.task_id, generationWait.signal, async (task) => {
            if (!isCurrent()) return;
            set({ task });
            await refreshStreamingState(task.progress?.completed_units ?? 0);
          });
          if (isCurrent()) set({ task: polled });
          return polled;
        }
      }, generationWait.signal);
      if (!isCurrent()) return;
      set({ task: completedTask });
      void get().loadFailedResources();

      if (completedTask.status === "failed" || completedTask.status === "interrupted") {
        const availablePreview = await getContentGenerationPreview(completedTask.task_id)
          .catch(() => getContentGenerationPartialPreview(completedTask.task_id))
          .catch(() => undefined);
        if (!isCurrent()) return;
        if (availablePreview) {
          set("is_partial" in availablePreview
            ? { partialPreview: availablePreview }
            : { preview: availablePreview, partialPreview: undefined });
        }
      }

      if (completedTask.status === "failed") {
        throw new Error(completedTask.errors.join("; ") || "内容生成任务执行失败。");
      }

      if (completedTask.status === "interrupted") {
        throw new Error(completedTask.progress?.interrupted_reason || "任务已中断，请重新生成。");
      }

      const preview = await getContentGenerationPreview(completedTask.task_id);
      if (!isCurrent()) return;
      previewDisabled = true;
      window.clearTimeout(retryTimers.preview);
      failedParts.delete("preview");
      updateRefreshError();
      await refreshStreamingState(0);
      if (!isCurrent()) return;
      set({ preview, loading: false });
    } catch (error) {
      if (!isActiveView()) return;
      set({ error: error instanceof Error ? error.message : "Unknown request error", loading: false });
    } finally {
      if (activeGenerationWait === generationWait) activeGenerationWait = undefined;
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
    const viewVersion = taskViewVersion;
    const isCurrent = () => viewVersion === taskViewVersion;
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
      failedResources: [],
      resourceRetryError: undefined,
      resourceUpdated: false,
      interactiveSessionId: undefined,
      exportResult: undefined
    });

    try {
      const task = await getContentGenerationTask(normalizedTaskId);
      if (!isCurrent()) {
        return;
      }
      const [eventsResult, unitsResult, previewResult] = await Promise.allSettled([
        getContentGenerationEvents(normalizedTaskId),
        getContentGenerationUnits(normalizedTaskId),
        getContentGenerationPreview(normalizedTaskId)
      ]);
      if (!isCurrent()) {
        return;
      }

      let partialPreview: PartialPreviewResponse | undefined;
      let previewFailed = false;
      if (previewResult.status === "fulfilled") {
        set({ preview: previewResult.value, partialPreview: undefined });
      } else {
        try {
          partialPreview = await getContentGenerationPartialPreview(normalizedTaskId);
        } catch {
          previewFailed = true;
        }
        if (!isCurrent()) {
          return;
        }
        set({ preview: undefined, partialPreview });
      }

      const detailsFailed =
        eventsResult.status === "rejected" || unitsResult.status === "rejected" || previewFailed;
      set({
        task,
        streamEvents: eventsResult.status === "fulfilled" ? eventsResult.value.events : [],
        renderUnits: unitsResult.status === "fulfilled" ? unitsResult.value.units : [],
        streamRefreshError: detailsFailed ? "部分进度或预览暂时无法更新。" : undefined,
        previewLookupLoading: false
      });

      if (task.status === "queued" || task.status === "running") {
        get().trackTask(normalizedTaskId);
      }
      void get().loadFailedResources();
    } catch (error) {
      if (!isCurrent()) {
        return;
      }
      set({
        error: error instanceof Error ? error.message : "加载任务失败，请稍后重试。",
        previewLookupLoading: false
      });
    }
  },

  trackTask(taskId) {
    get().stopStreamRefresh();
    let disposed = false;
    let unsubscribe: (() => void) | undefined;
    let pollTimer: number | undefined;
    let refreshing = false;
    let finishing = false;
    let controller: { retryFailed: () => void; dispose: () => void };
    const isCurrent = () => !disposed && get().task?.task_id === taskId;

    const refreshDetails = async () => {
      if (!isCurrent() || refreshing) {
        return;
      }
      refreshing = true;
      try {
        const [eventsResult, unitsResult, previewResult] = await Promise.allSettled([
          getContentGenerationEvents(taskId),
          getContentGenerationUnits(taskId),
          getContentGenerationPartialPreview(taskId)
        ]);
        if (!isCurrent()) {
          return;
        }
        if (eventsResult.status === "fulfilled") {
          set({ streamEvents: eventsResult.value.events });
        }
        if (unitsResult.status === "fulfilled") {
          set({ renderUnits: unitsResult.value.units });
        }
        if (previewResult.status === "fulfilled") {
          set({ partialPreview: previewResult.value });
        }
        const failed = [eventsResult, unitsResult, previewResult].some((item) => item.status === "rejected");
        set({ streamRefreshError: failed ? "部分进度或预览暂时无法更新。" : undefined });
      } finally {
        refreshing = false;
      }
    };

    const dispose = () => {
      disposed = true;
      unsubscribe?.();
      unsubscribe = undefined;
      window.clearTimeout(pollTimer);
    };

    const finish = async () => {
      try {
        const task = await getContentGenerationTask(taskId);
        if (!isCurrent()) {
          return;
        }
        set({ task });
        void get().loadFailedResources();
        if (task.status === "completed") {
          try {
            const preview = await getContentGenerationPreview(taskId);
            if (isCurrent()) {
              set({ preview, partialPreview: undefined, streamRefreshError: undefined });
            }
          } catch {
            if (isCurrent()) {
              set({ streamRefreshError: "最终预览暂时无法加载。" });
            }
          }
        } else {
          await refreshDetails();
        }
      } catch {
        if (isCurrent()) {
          set({ streamRefreshError: "无法获取任务最终状态。" });
        }
      } finally {
        dispose();
        if (activeStreamRefresh === controller) {
          activeStreamRefresh = undefined;
        }
      }
    };

    const poll = async () => {
      if (disposed || finishing) {
        return;
      }
      try {
        const task = await getContentGenerationTask(taskId);
        if (!isCurrent()) {
          return;
        }
        set({ task });
        await refreshDetails();
        if (task.status === "completed" || task.status === "failed" || task.status === "interrupted") {
          finishing = true;
          await finish();
          return;
        }
      } catch {
        if (isCurrent()) {
          set({ streamRefreshError: "无法获取任务进度，稍后将自动重试。" });
        }
      }
      pollTimer = window.setTimeout(() => void poll(), POLL_INTERVAL_MS);
    };

    controller = {
      retryFailed: () => {
        void refreshDetails();
      },
      dispose
    };
    activeStreamRefresh = controller;

    unsubscribe = subscribeContentGenerationStream(
      taskId,
      (snapshot) => {
        if (!isCurrent()) {
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
        if (snapshot.errors) {
          patch.errors = snapshot.errors;
        }
        const current = get().task;
        if (current) {
          set({ task: { ...current, ...patch } });
        }
        if (snapshot.units_count !== undefined || snapshot.events_count !== undefined) {
          void refreshDetails();
        }
        if (snapshot.done || snapshot.missing) {
          unsubscribe?.();
          unsubscribe = undefined;
          finishing = true;
          void finish();
        }
      },
      () => {
        unsubscribe?.();
        unsubscribe = undefined;
        if (!disposed && !finishing) {
          void poll();
        }
      }
    );
  },

  async loadFailedResources() {
    const taskId = get().task?.task_id;
    if (!taskId) {
      set({ failedResources: [] });
      return;
    }
    const requestId = ++failedResourcesRequestId;
    const viewVersion = taskViewVersion;
    try {
      const result = await getTaskFailedResources(taskId);
      if (viewVersion === taskViewVersion && requestId === failedResourcesRequestId && get().task?.task_id === taskId) {
        set({ failedResources: result.resources, resourceRetryError: undefined });
        const retrying = result.resources.find((resource) => resource.status === "retrying");
        if (retrying) void get().trackResourceRetry(retrying.resource_id);
      }
    } catch (error) {
      if (viewVersion === taskViewVersion && requestId === failedResourcesRequestId && get().task?.task_id === taskId) {
        set({ resourceRetryError: error instanceof Error ? error.message : "无法获取资源状态。" });
      }
    }
  },

  async retryResource(resourceId) {
    const task = get().task;
    if (!task) {
      return;
    }
    if (get().failedResources.some((item) => item.status === "retrying")) {
      return;
    }
    const taskId = task.task_id;
    const viewVersion = taskViewVersion;
    const isCurrent = () => viewVersion === taskViewVersion && get().task?.task_id === taskId;
    set({ resourceRetryError: undefined });

    try {
      await retryTaskResource(taskId, resourceId);
      if (!isCurrent()) return;
    } catch (error) {
      if (!isCurrent()) return;
      set({ resourceRetryError: error instanceof Error ? error.message : "提交重试失败。" });
      void get().loadFailedResources();
      return;
    }

    set({
      failedResources: get().failedResources.map((item) =>
        item.resource_id === resourceId
          ? { ...item, status: "retrying", retryable: false, retry_blocked_reason: "该资源正在重试。" }
          : item
      )
    });
    await get().trackResourceRetry(resourceId);
  },

  async trackResourceRetry(resourceId) {
    const taskId = get().task?.task_id;
    if (!taskId) return;
    if (activeResourcePolling?.taskId === taskId && activeResourcePolling.resourceId === resourceId) return;
    activeResourcePolling?.dispose();
    const viewVersion = taskViewVersion;
    const controller = { disposed: false };
    const isCurrent = () => !controller.disposed && viewVersion === taskViewVersion && get().task?.task_id === taskId;
    const dispose = () => {
      controller.disposed = true;
    };
    activeResourcePolling = { taskId, resourceId, dispose };
    const deadline = Date.now() + 180000;
    let requestErrors = 0;

    while (!controller.disposed && Date.now() < deadline) {
      await sleep(1500);
      if (!isCurrent()) {
        break;
      }
      try {
        const result = await getTaskFailedResources(taskId);
        if (!isCurrent()) {
          break;
        }
        requestErrors = 0;
        set({ failedResources: result.resources, resourceRetryError: undefined });
        const current = result.resources.find((item) => item.resource_id === resourceId);
        if (!current) {
          try {
            const refreshedTask = await getContentGenerationTask(taskId);
            if (!isCurrent()) {
              break;
            }
            set({ task: refreshedTask, resourceUpdated: true });
            try {
              const preview = await getContentGenerationPreview(taskId);
              if (isCurrent()) {
                set({ preview, partialPreview: undefined });
              }
            } catch {
              try {
                const partial = await getContentGenerationPartialPreview(taskId);
                if (isCurrent()) {
                  set({ preview: undefined, partialPreview: partial });
                }
              } catch {
                // Keep the existing preview; the resource file itself was regenerated.
              }
            }
          } catch (error) {
            if (!isCurrent()) break;
            set({
              resourceRetryError: error instanceof Error ? error.message : "资源已更新，但刷新任务失败。"
            });
          }
          break;
        }
        if (current.status === "failed" || current.status === "missing") {
          set({ resourceRetryError: current.error_message || "重新生成失败，请稍后重试。" });
          const refreshedTask = await getContentGenerationTask(taskId);
          if (isCurrent()) set({ task: refreshedTask });
          break;
        }
      } catch {
        if (!isCurrent()) break;
        requestErrors += 1;
        if (requestErrors >= 3) {
          set({ resourceRetryError: "无法获取重试状态，请稍后刷新查看结果。" });
          break;
        }
      }
    }

    if (isCurrent() && Date.now() >= deadline) {
      set({ resourceRetryError: "重新生成仍在进行，请稍后刷新查看结果。" });
      void get().loadFailedResources();
    }
    if (activeResourcePolling?.dispose === dispose) {
      activeResourcePolling = undefined;
    }
  },

  async exportTask(exportType) {
    const taskId = get().task?.task_id;
    if (!taskId) {
      set({ error: "No task is available to export." });
      return;
    }
    const viewVersion = taskViewVersion;
    const isCurrent = () => viewVersion === taskViewVersion && get().task?.task_id === taskId;
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
      if (!isCurrent()) return;
      const currentTask = get().task;
      if (exportResult.status === "success" && currentTask) {
        set({
          task: {
            ...currentTask,
            export_files: [
              ...currentTask.export_files.filter((file) => file.type !== exportType),
              { type: exportType, url: exportResult.file_url }
            ]
          },
          exportResult,
          resourceUpdated: false,
          loading: false
        });
      } else {
        set({ exportResult, loading: false });
      }
    } catch (error) {
      if (!isCurrent()) return;
      set({ error: error instanceof Error ? error.message : "导出失败，请稍后重试。", loading: false });
    }
  }
}));
