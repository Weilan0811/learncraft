import { useEffect, useState } from "react";

import { ContentGenerationForm } from "../components/generation/ContentGenerationForm";
import { ExportActions } from "../components/generation/ExportActions";
import { GenerationProgress } from "../components/generation/GenerationProgress";
import { PreviewErrorBoundary } from "../components/generation/PreviewErrorBoundary";
import { TaskPreviewLookup } from "../components/generation/TaskPreviewLookup";
import { LineIcon } from "../components/generation/icons";
import { useContentGenerationStore } from "../stores/contentGenerationStore";
import { ContentPreviewPage } from "./ContentPreviewPage";

type ServiceState = "checking" | "online" | "offline";

export function ContentGenerationPage() {
  const taskId = useContentGenerationStore((state) => state.task?.task_id);
  const preview = useContentGenerationStore((state) => state.preview ?? state.partialPreview);
  const stopStreamRefresh = useContentGenerationStore((state) => state.stopStreamRefresh);
  const [serviceState, setServiceState] = useState<ServiceState>("checking");

  useEffect(() => () => stopStreamRefresh(), [stopStreamRefresh]);

  useEffect(() => {
    let active = true;
    fetch("/health")
      .then((response) => {
        if (active) {
          setServiceState(response.ok ? "online" : "offline");
        }
      })
      .catch(() => {
        if (active) {
          setServiceState("offline");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const serviceLabel =
    serviceState === "online" ? "服务正常" : serviceState === "offline" ? "服务不可用" : "检查中";

  return (
    <main className="app-shell">
      <header className="workbench-header">
        <div className="brand-lockup">
          <span className="brand-mark">
            <LineIcon name="brand" size={16} />
          </span>
          <h1>内容生成工作台</h1>
          <span className="brand-divider" aria-hidden />
          <p className="brand-subtitle">基于大模型的教学内容创作工具</p>
        </div>
        <div className={`service-status service-status--${serviceState}`}>
          <span className="service-dot" aria-hidden />
          <span>{serviceLabel}</span>
        </div>
      </header>

      <section className="workspace">
        <aside className="panel form-panel">
          <ContentGenerationForm />
        </aside>

        <section className="panel preview-panel">
          <div className="preview-toolbar">
            <h2>预览与导出</h2>
            <div className="preview-toolbar-actions">
              <TaskPreviewLookup />
              <ExportActions />
            </div>
          </div>
          <GenerationProgress />
          <PreviewErrorBoundary taskId={taskId} preview={preview}>
            <ContentPreviewPage />
          </PreviewErrorBoundary>
        </section>
      </section>
    </main>
  );
}
