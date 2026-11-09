import { useContentGenerationStore } from "../../stores/contentGenerationStore";
import { LineIcon } from "./icons";

const stageLabels: Record<string, string> = {
  queued: "排队等待",
  running: "准备生成",
  normalizing: "整理请求",
  retrieving: "检索资料",
  planning: "规划大纲",
  validating_outline: "校验大纲",
  generating_direct_content: "生成内容",
  validating_direct_content: "校验内容",
  initializing_units: "初始化章节",
  retrieving_unit: "准备章节资料",
  generating_unit: "生成章节",
  validating_unit_spec: "校验章节结构",
  collecting_elements: "收集图片需求",
  generating_elements: "生成配图",
  merging_elements: "合并素材",
  validating_unit: "校验章节",
  rendering_unit: "渲染章节",
  unit_render_ready: "章节预览就绪",
  unit_completed: "章节完成",
  assembling_content: "汇总内容",
  validating_content: "校验整体内容",
  rendering: "渲染预览",
  completed: "生成完成",
  failed: "生成失败",
  interrupted: "任务已中断"
};

const eventLabels: Record<string, string> = {
  task_started: "任务开始",
  outline_ready: "大纲完成",
  unit_started: "章节开始",
  unit_spec_ready: "章节结构完成",
  element_ready: "素材完成",
  unit_render_ready: "章节预览完成",
  audio_segment_ready: "语音分段完成",
  direct_spec_ready: "内容结构完成",
  direct_render_ready: "预览渲染完成",
  task_completed: "任务完成",
  task_failed: "任务失败"
};

const statusMeta = {
  idle: { label: "等待开始", icon: "clock" as const },
  queued: { label: "排队中", icon: "clock" as const },
  running: { label: "生成中", icon: "clock" as const },
  completed: { label: "已完成", icon: "check" as const },
  failed: { label: "生成失败", icon: "alert" as const },
  interrupted: { label: "已中断", icon: "alert" as const }
};

type UiStatus = keyof typeof statusMeta;

function formatTime(value?: string | null): string {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("zh-CN");
}

function clampPercent(value: number, fallback: number): number {
  if (!Number.isFinite(value)) {
    return fallback;
  }
  return Math.min(100, Math.max(0, Math.round(value)));
}

export function GenerationProgress() {
  const task = useContentGenerationStore((state) => state.task);
  const loading = useContentGenerationStore((state) => state.loading);
  const error = useContentGenerationStore((state) => state.error);
  const streamRefreshError = useContentGenerationStore((state) => state.streamRefreshError);
  const renderUnits = useContentGenerationStore((state) => state.renderUnits);
  const streamEvents = useContentGenerationStore((state) => state.streamEvents);
  const retryStreamRefresh = useContentGenerationStore((state) => state.retryStreamRefresh);
  const retryLastTask = useContentGenerationStore((state) => state.retryLastTask);
  const lastRequest = useContentGenerationStore((state) => state.lastRequest);

  const status: UiStatus = task?.status ?? (loading ? "running" : "idle");
  const meta = statusMeta[status];
  const progress = task?.progress;
  const stage = progress?.display_stage || progress?.stage || status;
  const stageLabel = stageLabels[stage] ?? stage;
  const fallbackPercent = status === "completed" ? 100 : 0;
  const percent = clampPercent(
    typeof progress?.percent === "number" ? progress.percent : fallbackPercent,
    fallbackPercent
  );
  const unitText =
    typeof progress?.completed_units === "number" && typeof progress?.total_units === "number"
      ? `${progress.completed_units} / ${progress.total_units}`
      : "";
  const renderedUnits = renderUnits.filter((unit) => unit.status === "rendered").length;
  const failedResources = progress?.resource_summary?.failed ?? 0;
  const retryingResources = progress?.resource_summary?.retrying ?? 0;
  const latestEvent = streamEvents.at(-1);
  const latestEventLabel = latestEvent ? eventLabels[latestEvent.type] ?? latestEvent.type : "-";
  const currentNode = task?.current_node || progress?.current_node || "-";
  const knowledgeMessage =
    progress?.knowledge_base?.message || task?.knowledge_base?.message || "未使用知识库资料";
  const taskError = status === "failed" || status === "interrupted" || !task ? error : undefined;
  const isRunning = status === "queued" || status === "running";
  const label = status === "idle" && taskError ? "请求失败" : meta.label;
  const icon = status === "idle" && taskError ? "alert" : meta.icon;
  const updatedAt = formatTime(task?.updated_at);
  const taskErrors = task?.errors?.filter(Boolean) ?? [];

  if (!task && !taskError && !streamRefreshError) {
    return null;
  }

  return (
    <section className={`task-status task-status--${status}`}>
      <div className="task-status-top">
        <span className="task-status-icon">
          <LineIcon name={icon} size={16} />
        </span>
        <div className="task-status-copy">
          <strong>{label}</strong>
          <span>{stageLabel}</span>
        </div>
        {isRunning ? <span className="task-status-percent">{percent}%</span> : null}
      </div>

      {isRunning ? (
        <div className="task-progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}>
          <span style={{ width: `${percent}%` }} />
        </div>
      ) : null}

      {task ? (
        <div className="task-status-meta">
          {unitText ? <span>章节 {unitText}</span> : null}
          <span>已渲染 {renderedUnits}</span>
          {failedResources > 0 ? <span className="is-warning">{failedResources} 个资源失败</span> : null}
          {retryingResources > 0 ? <span>{retryingResources} 个资源重试中</span> : null}
          {status === "completed" && failedResources === 0 ? <span className="is-success">无失败资源</span> : null}
        </div>
      ) : null}

      {taskError ? (
        <div className="task-status-error">
          <span>{taskError}</span>
          {lastRequest ? (
            <button type="button" className="link-button" onClick={() => void retryLastTask()} disabled={loading}>
              {loading ? "正在重试…" : "重新生成"}
            </button>
          ) : null}
        </div>
      ) : null}

      {streamRefreshError ? (
        <div className="task-status-error">
          <span>{streamRefreshError}</span>
          <button type="button" className="link-button" onClick={retryStreamRefresh}>
            重新加载
          </button>
        </div>
      ) : null}

      {task ? (
        <details className="tech-details">
          <summary>查看详情</summary>
          <dl>
            <div>
              <dt>任务编号</dt>
              <dd>{task.task_id}</dd>
            </div>
            <div>
              <dt>当前节点</dt>
              <dd>{currentNode}</dd>
            </div>
            <div>
              <dt>阶段</dt>
              <dd>{stage}</dd>
            </div>
            <div>
              <dt>最新事件</dt>
              <dd>{latestEventLabel}</dd>
            </div>
            <div>
              <dt>更新时间</dt>
              <dd>{updatedAt || "-"}</dd>
            </div>
            <div>
              <dt>知识库</dt>
              <dd>{knowledgeMessage}</dd>
            </div>
          </dl>
          {taskErrors.length > 0 ? (
            <ul className="tech-errors">
              {taskErrors.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))}
            </ul>
          ) : null}
        </details>
      ) : null}
    </section>
  );
}
