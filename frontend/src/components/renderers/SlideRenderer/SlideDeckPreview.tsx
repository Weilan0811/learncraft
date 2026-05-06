import { useState } from "react";

import type { SlideRenderModel } from "../../../types/slide";

interface SlideDeckPreviewProps {
  model: SlideRenderModel;
}

export function SlideDeckPreview({ model }: SlideDeckPreviewProps) {
  // TODO(MVP-slide-renderer): Replace JSON preview with scene-content-kit
  // SceneRenderer, zoom controls, page thumbnails, and asset rendering.
  const [index, setIndex] = useState(0);
  const page = model.pages[index]?.page;

  return (
    <article className="slide-renderer">
      <header>
        <p className="eyebrow">Slide Preview</p>
        <h2>{model.title}</h2>
      </header>
      <div className="slide-stage">
        <pre>{JSON.stringify(page, null, 2)}</pre>
      </div>
      <div className="slide-controls">
        <button type="button" disabled={index === 0} onClick={() => setIndex((value) => value - 1)}>
          上一页
        </button>
        <span>
          {index + 1} / {model.pages.length}
        </span>
        <button type="button" disabled={index >= model.pages.length - 1} onClick={() => setIndex((value) => value + 1)}>
          下一页
        </button>
      </div>
    </article>
  );
}
