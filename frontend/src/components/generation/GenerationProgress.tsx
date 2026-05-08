import { useContentGenerationStore } from "../../stores/contentGenerationStore";

function formatPercent(percent?: number) {
  if (typeof percent !== "number") {
    return "0%";
  }
  return `${Math.round(percent)}%`;
}

export function GenerationProgress() {
  const { task, loading, error } = useContentGenerationStore();
  const progress = task?.progress;
  const stage = progress?.display_stage || progress?.stage || task?.status || (loading ? "running" : "idle");
  const percent = formatPercent(progress?.percent);
  const unitText =
    typeof progress?.completed_units === "number" && typeof progress?.total_units === "number" && progress.total_units > 0
      ? `${progress.completed_units} / ${progress.total_units}`
      : "-";

  return (
    <section className="status-strip">
      <div>
        <span>状态</span>
        <strong>{task?.status ?? (loading ? "running" : "idle")}</strong>
      </div>
      <div>
        <span>阶段</span>
        <strong>{stage}</strong>
      </div>
      <div>
        <span>进度</span>
        <strong>{percent}</strong>
      </div>
      <div>
        <span>单元</span>
        <strong>{unitText}</strong>
      </div>
      <div>
        <span>节点</span>
        <strong>{task?.current_node || progress?.current_node || "-"}</strong>
      </div>
      <div>
        <span>任务</span>
        <strong>{task?.task_id ?? "尚未创建"}</strong>
      </div>
      {error ? <p className="error-text">{error}</p> : null}
    </section>
  );
}
