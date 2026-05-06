interface MindmapElementProps {
  title: string;
  markdown: string;
}

export function MindmapElement({ title, markdown }: MindmapElementProps) {
  return (
    <div className="content-block mindmap-placeholder">
      <h4>{title}</h4>
      <pre>{markdown}</pre>
    </div>
  );
}
