import type { TaskResult } from "../types/export";

interface TaskHistoryPageProps {
  tasks: TaskResult[];
}

export function TaskHistoryPage({ tasks }: TaskHistoryPageProps) {
  // TODO(MVP-task-history): Load persisted task history, support filters by
  // content_type/status, and allow reopening preview/export results.
  return (
    <section className="task-history">
      <h2>任务历史</h2>
      {tasks.length === 0 ? (
        <p>暂无历史任务。</p>
      ) : (
        <ul>
          {tasks.map((task) => (
            <li key={task.task_id}>
              <span>{task.task_id}</span>
              <strong>{task.status}</strong>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
