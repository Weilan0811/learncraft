import type { RenderBlock } from "../../../../types/lecture";

interface QuizBlockProps {
  block: RenderBlock;
}

export function QuizBlock({ block }: QuizBlockProps) {
  return <div className="content-block">测验占位：{block.title}</div>;
}
