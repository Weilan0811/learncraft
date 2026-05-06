import type { RenderBlock } from "../../../../types/lecture";
import { ChartElement } from "../../../elements/ChartElement";

interface ChartBlockProps {
  block: RenderBlock;
}

export function ChartBlock({ block }: ChartBlockProps) {
  return <ChartElement title={block.title ?? "图表"} />;
}
