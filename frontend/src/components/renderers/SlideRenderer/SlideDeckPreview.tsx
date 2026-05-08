import { useState } from "react";
import { SceneRenderer } from "../../../../scene-content-kit";
import type { KitScene, KitSlideElement, KitSlideBackground, KitTheme } from "../../../../scene-content-kit";
import type { SlideRenderModel } from "../../../types/slide";

interface SlidePageData {
  id: string;
  title: string;
  width: number;
  height: number;
  background?: KitSlideBackground;
  theme?: KitTheme;
  elements?: Array<{
    id: string;
    type: string;
    left: number;
    top: number;
    width: number;
    height: number;
    rotate: number;
    content?: string;
    url?: string;
    src?: string;
    defaultFontName?: string;
    defaultColor?: string;
    fontSize?: number;
    bold?: boolean;
  }>;
  speakerNotes?: string;
}

function adaptSlidePage(pageData: SlidePageData, index: number): KitScene {
  const elements: KitSlideElement[] = (pageData.elements || []).map((el) => {
    if (el.type === "text") {
      return {
        id: el.id,
        type: "text" as const,
        left: el.left,
        top: el.top,
        width: el.width,
        height: el.height,
        rotate: el.rotate,
        content: el.content || "",
        defaultFontName: el.defaultFontName,
        defaultColor: el.defaultColor,
        fontSize: el.fontSize,
        bold: el.bold,
      };
    }
    if (el.type === "image") {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";
      const imageUrl = el.src || el.url || "";
      const src = imageUrl && !imageUrl.startsWith("http") ? `${apiBaseUrl}${imageUrl}` : imageUrl;
      return {
        id: el.id,
        type: "image" as const,
        left: el.left,
        top: el.top,
        width: el.width,
        height: el.height,
        rotate: el.rotate,
        src,
      };
    }
    return {
      id: el.id,
      type: "shape" as const,
      left: el.left,
      top: el.top,
      width: el.width,
      height: el.height,
      rotate: el.rotate,
      fill: "#e5e7eb",
    };
  });

  const theme: KitTheme = pageData.theme || {
    backgroundColor: "#ffffff",
    themeColors: ["#2563eb", "#0f766e"],
    fontColor: "#111827",
    fontName: "Arial",
  };

  const background: KitSlideBackground = pageData.background || {
    type: "solid",
    color: "#ffffff",
  };

  return {
    id: pageData.id,
    title: pageData.title,
    type: "slide",
    order: index,
    content: {
      type: "slide",
      canvas: {
        id: pageData.id,
        viewportSize: pageData.width || 960,
        viewportRatio: (pageData.width || 960) / (pageData.height || 540),
        theme,
        elements,
        background,
      },
    },
  };
}

interface SlideDeckPreviewProps {
  model: SlideRenderModel;
}

export function SlideDeckPreview({ model }: SlideDeckPreviewProps) {
  const [index, setIndex] = useState(0);
  const pages = model.pages || [];
  const currentPage = pages[index];

  if (!currentPage) {
    return (
      <article className="slide-renderer">
        <header>
          <p className="eyebrow">Slide Preview</p>
          <h2>{model.title}</h2>
        </header>
        <div className="slide-stage empty">暂无幻灯片内容</div>
      </article>
    );
  }

  const pageData = currentPage.page as unknown as SlidePageData;
  const scene = adaptSlidePage(pageData, index);

  return (
    <article className="slide-renderer">
      <header>
        <p className="eyebrow">Slide Preview</p>
        <h2>{model.title}</h2>
      </header>
      <div className="slide-stage">
        <SceneRenderer scene={scene} />
      </div>
      <div className="slide-controls">
        <button type="button" disabled={index === 0} onClick={() => setIndex((v) => v - 1)}>
          上一页
        </button>
        <span>
          {index + 1} / {pages.length}
        </span>
        <button type="button" disabled={index >= pages.length - 1} onClick={() => setIndex((v) => v + 1)}>
          下一页
        </button>
      </div>
      {pageData.speakerNotes && (
        <div className="speaker-notes">
          <h4>演讲者备注</h4>
          <p>{pageData.speakerNotes}</p>
        </div>
      )}
    </article>
  );
}
