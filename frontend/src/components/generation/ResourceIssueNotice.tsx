import { useContentGenerationStore } from "../../stores/contentGenerationStore";
import type { TaskResource } from "../../types/export";
import { LineIcon } from "./icons";

interface ResourceIssueNoticeProps {
  resource: TaskResource;
}

export function ResourceIssueNotice({ resource }: ResourceIssueNoticeProps) {
  const retryResource = useContentGenerationStore((state) => state.retryResource);
  const anyRetrying = useContentGenerationStore((state) =>
    state.failedResources.some((item) => item.status === "retrying")
  );
  const retrying = resource.status === "retrying";
  const reason = retrying
    ? "正在重新生成，完成后会自动刷新预览。"
    : resource.error_message || resource.retry_blocked_reason || "资源生成失败。";

  return (
    <div className={`resource-issue${retrying ? " is-retrying" : ""}`}>
      <LineIcon name={retrying ? "clock" : "alert"} size={14} />
      <div className="resource-issue-copy">
        <strong>{retrying ? "正在重新生成" : "资源生成失败"}</strong>
        <span>{reason}</span>
      </div>
      {!retrying ? (
        <button
          type="button"
          className="link-button"
          disabled={!resource.retryable || anyRetrying}
          title={resource.retry_blocked_reason ?? undefined}
          onClick={() => void retryResource(resource.resource_id)}
        >
          {anyRetrying ? "重试中…" : "重新生成"}
        </button>
      ) : null}
    </div>
  );
}
