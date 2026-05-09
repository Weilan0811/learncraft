import { useEffect, useMemo, useRef } from "react";
import { Transformer } from "markmap-lib";
import * as markmapView from "markmap-view";
import { Markmap, loadCSS, loadJS } from "markmap-view";

import { normalizeMindmapMarkdown } from "../../utils/markmap";

interface MindmapElementProps {
  title: string;
  markdown: string;
}

const transformer = new Transformer();

export function MindmapElement({ title, markdown }: MindmapElementProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const markmapRef = useRef<Markmap | null>(null);

  const normalizedMarkdown = useMemo(
    () => normalizeMindmapMarkdown(markdown, title || "思维导图"),
    [markdown, title],
  );

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl) return;

    const { root, features } = transformer.transform(normalizedMarkdown);
    const assets = transformer.getUsedAssets(features);

    if (assets.styles) {
      loadCSS(assets.styles);
    }

    if (assets.scripts) {
      loadJS(assets.scripts, {
        getMarkmap: () => markmapView,
      });
    }

    markmapRef.current?.destroy();

    const mm = Markmap.create(
      svgEl,
      {
        autoFit: true,
        fitRatio: 0.92,
        initialExpandLevel: 3,
        duration: 250,
        maxWidth: 260,
        spacingHorizontal: 72,
        spacingVertical: 8,
        paddingX: 12,
      },
      root,
    );

    markmapRef.current = mm;

    requestAnimationFrame(() => {
      void mm.fit();
    });

    return () => {
      mm.destroy();
      if (markmapRef.current === mm) {
        markmapRef.current = null;
      }
    };
  }, [normalizedMarkdown]);

  return (
    <div className="content-block mindmap-element">
      <div className="mindmap-header">
        <h4>{title}</h4>
      </div>

      <div className="mindmap-canvas">
        <svg ref={svgRef} className="mindmap-svg" />
      </div>

      <details className="mindmap-source">
        <summary>查看 Markdown 原文</summary>
        <pre>{normalizedMarkdown}</pre>
      </details>
    </div>
  );
}