interface MindmapElementProps {
  title: string;
  markdown: string;
}

export function MindmapElement({ title, markdown }: MindmapElementProps) {
  // TODO(P1-mindmap): Render Markdown with Markmap and expose SVG/PNG export
  // for lecture print mode and slide image embedding.
  return (
    <div className="content-block mindmap-placeholder">
      <h4>{title}</h4>
      <pre>{markdown}</pre>
    </div>
  );
}
