interface MindmapElementProps {
  title: string;
  markdown: string;
}

export function MindmapElement({ title, markdown }: MindmapElementProps) {
  const lines = markdown.trim().split("\n");

  return (
    <div className="content-block mindmap-element">
      <h4>{title}</h4>
      <div className="mindmap-content">
        {lines.map((line, index) => {
          const depth = (line.match(/^#+/) || [""])[0].length;
          const text = line.replace(/^#+\s*/, "");
          if (!text.trim()) return null;
          return (
            <div
              key={index}
              className="mindmap-node"
              style={{ paddingLeft: `${depth * 16}px` }}
            >
              <span className="mindmap-bullet">•</span>
              <span className="mindmap-text">{text}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
