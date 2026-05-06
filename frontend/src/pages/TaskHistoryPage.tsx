import type { TaskResult } from "../types/export";

interface TaskHistoryPageProps {
  tasks: TaskResult[];
}

export function TaskHistoryPage({ tasks }: TaskHistoryPageProps) {
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
