import { ContentGenerationForm } from "../components/generation/ContentGenerationForm";
import { ExportActions } from "../components/generation/ExportActions";
import { GenerationProgress } from "../components/generation/GenerationProgress";
import { PreviewErrorBoundary } from "../components/generation/PreviewErrorBoundary";
import { TaskPreviewLookup } from "../components/generation/TaskPreviewLookup";
import { useContentGenerationStore } from "../stores/contentGenerationStore";
import { ContentPreviewPage } from "./ContentPreviewPage";

export function ContentGenerationPage() {
  const taskId = useContentGenerationStore((state) => state.task?.task_id);
  const preview = useContentGenerationStore((state) => state.preview ?? state.partialPreview);

  return (
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
  );
}
