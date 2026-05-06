import { useContentGenerationStore } from "../../stores/contentGenerationStore";

export function GenerationProgress() {
  const { task, loading, error } = useContentGenerationStore();

  return (
    <section className="status-strip">
      <div>
        <span>状态</span>
        <strong>{loading ? "running" : task?.status ?? "idle"}</strong>
      </div>
      <div>
        <span>任务</span>
        <strong>{task?.task_id ?? "尚未创建"}</strong>
      </div>
      {error ? <p className="error-text">{error}</p> : null}
    </section>
  );
}
