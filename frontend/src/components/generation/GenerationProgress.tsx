import { useContentGenerationStore } from "../../stores/contentGenerationStore";

function formatPercent(percent?: number) {
  if (typeof percent !== "number") {
    return "0%";
  }
  return `${Math.round(percent)}%`;
}

export function GenerationProgress() {
  const { task, loading, error, renderUnits, streamEvents } = useContentGenerationStore();
  const progress = task?.progress;
  const stage = progress?.display_stage || progress?.stage || task?.status || (loading ? "running" : "idle");
  const percent = formatPercent(progress?.percent);
  const unitText =
    typeof progress?.completed_units === "number" && typeof progress?.total_units === "number" && progress.total_units > 0
      ? `${progress.completed_units} / ${progress.total_units}`
      : "-";
  const renderedUnits = renderUnits.filter((unit) => unit.status === "rendered").length;
  const latestEvent = streamEvents.at(-1);

  return (
    <section className="status-strip">
      <div>
        <span>Status</span>
        <strong>{task?.status ?? (loading ? "running" : "idle")}</strong>
      </div>
      <div>
        <span>Stage</span>
        <strong>{stage}</strong>
      </div>
      <div>
        <span>Progress</span>
        <strong>{percent}</strong>
      </div>
      <div>
        <span>Units</span>
        <strong>{unitText}</strong>
      </div>
      <div>
        <span>Rendered</span>
        <strong>{renderedUnits}</strong>
      </div>
      <div>
        <span>Node</span>
        <strong>{task?.current_node || progress?.current_node || "-"}</strong>
      </div>
      <div>
        <span>Latest event</span>
        <strong>{latestEvent?.type ?? "-"}</strong>
      </div>
      <div>
        <span>Task</span>
        <strong>{task?.task_id ?? "not created"}</strong>
      </div>
      {error ? <p className="error-text">{error}</p> : null}
    </section>
  );
}
