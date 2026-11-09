import { useCallback, useEffect, useRef, useState } from "react";

import { listContentGenerationTasks } from "../api/contentGenerationApi";
import { LineIcon } from "../components/generation/icons";
import type { MvpContentType } from "../types/content";
import type { TaskListItem, TaskListResponse, TaskStatus } from "../types/export";

const PAGE_SIZE = 10;

const typeOptions: Array<{ value: MvpContentType; label: string }> = [
  { value: "lecture", label: "讲义" },
  { value: "slide_deck", label: "幻灯片" },
  { value: "social_post", label: "图文推文" },
  { value: "podcast_script", label: "播客文稿" },
  { value: "interactive_html", label: "互动讲义" }
];

const statusOptions: Array<{ value: TaskStatus; label: string }> = [
  { value: "queued", label: "排队中" },
  { value: "running", label: "生成中" },
  { value: "completed", label: "已完成" },
  { value: "failed", label: "失败" },
  { value: "interrupted", label: "已中断" }
];

const typeLabels: Record<MvpContentType, string> = {
  lecture: "讲义",
  slide_deck: "幻灯片",
  social_post: "图文推文",
  podcast_script: "播客文稿",
  interactive_html: "互动讲义"
};

const statusLabels: Record<TaskStatus, string> = {
  queued: "排队中",
  running: "生成中",
  completed: "已完成",
  failed: "失败",
  interrupted: "已中断"
};

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  });
}

function openTask(taskId: string) {
  window.location.hash = `#task=${encodeURIComponent(taskId)}`;
}

export function TaskHistoryPage() {
  const [contentType, setContentType] = useState<MvpContentType | "">("");
  const [status, setStatus] = useState<TaskStatus | "">("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<TaskListResponse>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const requestIdRef = useRef(0);

  const load = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(undefined);
    try {
      const response = await listContentGenerationTasks({
        page,
        page_size: PAGE_SIZE,
        content_type: contentType || undefined,
        status: status || undefined
      });
      if (requestId === requestIdRef.current) {
        setData(response);
      }
    } catch (requestError) {
      if (requestId === requestIdRef.current) {
        setError(requestError instanceof Error ? requestError.message : "加载历史任务失败。");
      }
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, [page, contentType, status]);

  useEffect(() => {
    void load();
  }, [load]);

  const items: TaskListItem[] = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function changeContentType(value: MvpContentType | "") {
    setContentType(value);
    setPage(1);
  }

  function changeStatus(value: TaskStatus | "") {
    setStatus(value);
    setPage(1);
  }

  return (
    <section className="history-workspace">
      <div className="history-panel">
        <div className="history-toolbar">
          <div>
            <h2>历史记录</h2>
            <p>{data ? `共 ${total} 个任务` : "查看已创建的内容生成任务"}</p>
          </div>
          <div className="history-filters">
            <select
              aria-label="按内容类型筛选"
              value={contentType}
              onChange={(event) => changeContentType(event.target.value as MvpContentType | "")}
            >
              <option value="">全部类型</option>
              {typeOptions.map((option) => (
                <option value={option.value} key={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <select
              aria-label="按任务状态筛选"
              value={status}
              onChange={(event) => changeStatus(event.target.value as TaskStatus | "")}
            >
              <option value="">全部状态</option>
              {statusOptions.map((option) => (
                <option value={option.value} key={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <button type="button" className="toolbar-button" onClick={() => void load()} disabled={loading}>
              <LineIcon name="refresh" size={14} />
              {loading ? "刷新中…" : "刷新"}
            </button>
          </div>
        </div>

        {error ? (
          <div className="history-error">
            <span>{error}</span>
            <button type="button" className="link-button" onClick={() => void load()}>
              重试
            </button>
          </div>
        ) : null}

        {loading && !data ? <div className="history-loading">正在加载历史任务…</div> : null}

        {!loading && data && items.length === 0 ? (
          <div className="history-empty">
            <LineIcon name="fileText" size={48} />
            <h3>暂无历史任务</h3>
            <p>完成一次内容生成后，任务会出现在这里。</p>
          </div>
        ) : null}

        {items.length > 0 ? (
          <div className="history-table">
            <div className="history-table-head" aria-hidden>
              <span>主题</span>
              <span>类型</span>
              <span>状态</span>
              <span>创建时间</span>
              <span>更新时间</span>
              <span>异常资源</span>
              <span />
            </div>
            {items.map((item) => (
              <button
                type="button"
                className="history-row"
                onClick={() => openTask(item.task_id)}
                key={item.task_id}
              >
                <span className="history-topic">
                  <strong>{item.topic || "未命名任务"}</strong>
                  <small>{item.task_id}</small>
                </span>
                <span>{typeLabels[item.content_type] ?? item.content_type}</span>
                <span className={`history-status history-status--${item.status}`}>
                  <i aria-hidden />
                  {statusLabels[item.status] ?? item.status}
                </span>
                <span className="history-time">{formatTime(item.created_at)}</span>
                <span className="history-time">{formatTime(item.updated_at)}</span>
                <span className={item.failed_resource_count > 0 ? "history-failed" : "history-none"}>
                  {item.failed_resource_count > 0 ? `${item.failed_resource_count} 个` : "—"}
                </span>
                <span className="history-open" aria-hidden>
                  <LineIcon name="chevronRight" size={14} />
                </span>
              </button>
            ))}
          </div>
        ) : null}

        {total > 0 ? (
          <div className="history-pagination">
            <span>
              第 {page} / {totalPages} 页
            </span>
            <button
              type="button"
              disabled={page <= 1 || loading}
              onClick={() => setPage((current) => Math.max(1, current - 1))}
            >
              上一页
            </button>
            <button
              type="button"
              disabled={page >= totalPages || loading}
              onClick={() => setPage((current) => current + 1)}
            >
              下一页
            </button>
          </div>
        ) : null}
      </div>
    </section>
  );
}
