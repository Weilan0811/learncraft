import { InteractiveHtmlRenderer } from "../components/renderers/InteractiveHtmlRenderer";
import { LectureRenderer } from "../components/renderers/LectureRenderer";
import { PodcastRenderer } from "../components/renderers/PodcastRenderer";
import { SlideDeckPreview } from "../components/renderers/SlideRenderer/SlideDeckPreview";
import { SocialPostPreviewRenderer } from "../components/renderers/SocialPostRenderer";
import { useContentGenerationStore } from "../stores/contentGenerationStore";

export function ContentPreviewPage() {
  const preview = useContentGenerationStore((state) => state.preview);
  const partialPreview = useContentGenerationStore((state) => state.partialPreview);
  const activePreview = preview ?? partialPreview;

  if (!activePreview) {
    return (
      <section className="empty-preview">
        <h2>预览</h2>
        <p>提交生成任务后，这里会展示后端返回的预览内容。</p>
      </section>
    );
  }

  if (activePreview.render_model.render_type === "slide_deck") {
    return <SlideDeckPreview model={activePreview.render_model} />;
  }

  if (activePreview.render_model.render_type === "social_post") {
    return <SocialPostPreviewRenderer model={activePreview.render_model} />;
  }

  if (activePreview.render_model.render_type === "podcast_script") {
    return <PodcastRenderer model={activePreview.render_model} />;
  }

  if (activePreview.render_model.render_type === "interactive_html_page") {
    return <InteractiveHtmlRenderer model={activePreview.render_model} />;
  }

  return <LectureRenderer model={activePreview.render_model} />;
}
