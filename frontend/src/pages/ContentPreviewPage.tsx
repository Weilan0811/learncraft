import { LectureRenderer } from "../components/renderers/LectureRenderer";
import { SlideDeckPreview } from "../components/renderers/SlideRenderer/SlideDeckPreview";
import { useContentGenerationStore } from "../stores/contentGenerationStore";

export function ContentPreviewPage() {
  // TODO(MVP-preview): Add editable preview modes and section-level
  // regeneration hooks once backend stores content_spec/render_model snapshots.
  const preview = useContentGenerationStore((state) => state.preview);
  const partialPreview = useContentGenerationStore((state) => state.partialPreview);
  const activePreview = preview ?? partialPreview;

  if (!activePreview) {
    return (
      <section className="empty-preview">
        <h2>预览</h2>
        <p>提交生成任务后，这里会展示符合统一 schema 的占位渲染模型。</p>
      </section>
    );
  }

  if (activePreview.render_model.render_type === "slide_deck") {
    return <SlideDeckPreview model={activePreview.render_model} />;
  }

  return <LectureRenderer model={activePreview.render_model} />;
}
