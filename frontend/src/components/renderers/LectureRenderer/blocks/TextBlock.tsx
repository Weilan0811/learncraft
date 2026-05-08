import type { RenderBlock } from "../../../../types/lecture";

interface TextBlockProps {
  block: RenderBlock;
}

export function TextBlock({ block }: TextBlockProps) {
  const paragraphs = (block.content ?? "").split(/\n\n+/);

  return (
    <div className="content-block text-block">
      {block.title ? <h4>{block.title}</h4> : null}
      {paragraphs.map((p, i) => (
        <p key={i}>{p}</p>
      ))}
    </div>
  );
}
