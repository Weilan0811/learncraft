import { InteractiveHtmlRenderer } from "../components/renderers/InteractiveHtmlRenderer";
import { LectureRenderer } from "../components/renderers/LectureRenderer";
import { PodcastRenderer } from "../components/renderers/PodcastRenderer";
import { SlideDeckPreview } from "../components/renderers/SlideRenderer/SlideDeckPreview";
import { SocialPostPreviewRenderer } from "../components/renderers/SocialPostRenderer";
import { LineIcon } from "../components/generation/icons";
import { useContentGenerationStore } from "../stores/contentGenerationStore";

export function ContentPreviewPage() {
  const preview = useContentGenerationStore((state) => state.preview);
  const partialPreview = useContentGenerationStore((state) => state.partialPreview);
  const task = useContentGenerationStore((state) => state.task);
  const loading = useContentGenerationStore((state) => state.loading);
  const activePreview = preview ?? partialPreview;

  if (!activePreview) {
    const running = loading || task?.status === "queued" || task?.status === "running";
    return (
      <section className="empty-preview">
        <span className="empty-preview-icon">
          <LineIcon name={running ? "clock" : "fileText"} size={56} />
        </span>
        <h2>{running ? "正在生成内容" : "暂无生成内容"}</h2>
        <p>{running ? "章节完成后会逐步显示预览。" : "完成左侧配置后，生成结果会显示在这里。"}</p>
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
