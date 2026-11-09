import { FormEvent, useState } from "react";

import { useContentGenerationStore } from "../../stores/contentGenerationStore";
import { LineIcon } from "./icons";

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
    <details className="task-lookup">
      <summary>
        <LineIcon name="search" size={14} />
        <span>打开已有任务</span>
      </summary>
      <form className="task-lookup-form" onSubmit={handleSubmit}>
        <input
          aria-label="任务编号"
          value={taskId}
          placeholder="task_xxxxxxxxxxxx"
          onChange={(event) => setTaskId(event.target.value)}
        />
        <button type="submit" className="toolbar-button" disabled={previewLookupLoading || loading || !taskId.trim()}>
          {previewLookupLoading ? "读取中…" : "读取"}
        </button>
      </form>
    </details>
  );
}
