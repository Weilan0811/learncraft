import type { RenderBlock } from "../../../../types/lecture";

interface TableBlockProps {
  block: RenderBlock;
}

export function TableBlock({ block }: TableBlockProps) {
  return <div className="content-block">表格占位：{block.title}</div>;
}
