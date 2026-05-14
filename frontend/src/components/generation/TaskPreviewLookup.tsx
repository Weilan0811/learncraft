import { FormEvent, useState } from "react";

import { useContentGenerationStore } from "../../stores/contentGenerationStore";

export function TaskPreviewLookup() {
  const [taskId, setTaskId] = useState("");
  const loadPreviewByTaskId = useContentGenerationStore((state) => state.loadPreviewByTaskId);
  const previewLookupLoading = useContentGenerationStore((state) => state.previewLookupLoading);
  const loading = useContentGenerationStore((state) => state.loading);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadPreviewByTaskId(taskId);
  }

  return (
    <form className="task-preview-lookup" onSubmit={handleSubmit}>
      <div>
        <h2>查询历史预览</h2>
        <p>输入后端已保存的 task_id，读取该任务此前生成的 preview。</p>
      </div>

      <label>
        Task ID
        <input
          value={taskId}
          placeholder="task_xxxxxxxxxxxx"
          onChange={(event) => setTaskId(event.target.value)}
        />
      </label>

      <button type="submit" disabled={previewLookupLoading || loading || !taskId.trim()}>
        {previewLookupLoading ? "查询中..." : "查询预览"}
      </button>
    </form>
  );
}
