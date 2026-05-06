import type { RenderBlock } from "../../../../types/lecture";

interface TextBlockProps {
  block: RenderBlock;
}

export function TextBlock({ block }: TextBlockProps) {
  return (
    <div className="content-block text-block">
      {block.title ? <h4>{block.title}</h4> : null}
      <p>{block.content ?? "文本内容将在后续 Generator 实现后填充。"}</p>
    </div>
  );
}
