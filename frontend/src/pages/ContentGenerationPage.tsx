import { ContentGenerationForm } from "../components/generation/ContentGenerationForm";
import { ExportActions } from "../components/generation/ExportActions";
import { GenerationProgress } from "../components/generation/GenerationProgress";
import { PreviewErrorBoundary } from "../components/generation/PreviewErrorBoundary";
import { TaskPreviewLookup } from "../components/generation/TaskPreviewLookup";
import { ContentPreviewPage } from "./ContentPreviewPage";

export function ContentGenerationPage() {
  return (
    <main className="app-shell">
      <section className="workspace">
        <div className="panel form-panel">
          <div className="panel-heading">
            <p className="eyebrow">Content Generator</p>
            <h1>内容生成组件</h1>
          </div>
          <ContentGenerationForm />
          <TaskPreviewLookup />
        </div>
        <div className="panel preview-panel">
          <GenerationProgress />
          <PreviewErrorBoundary>
            <ContentPreviewPage />
          </PreviewErrorBoundary>
          <ExportActions />
        </div>
      </section>
    </main>
  );
}
