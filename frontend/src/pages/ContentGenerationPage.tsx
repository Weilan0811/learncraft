import { ContentGenerationForm } from "../components/generation/ContentGenerationForm";
import { ExportActions } from "../components/generation/ExportActions";
import { GenerationProgress } from "../components/generation/GenerationProgress";
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
        </div>
        <div className="panel preview-panel">
          <GenerationProgress />
          <ContentPreviewPage />
          <ExportActions />
        </div>
      </section>
    </main>
  );
}
