import type { RenderBlock } from "../../../../types/lecture";
import { MindmapElement } from "../../../elements/MindmapElement";

interface MindmapBlockProps {
  block: RenderBlock;
}

export function MindmapBlock({ block }: MindmapBlockProps) {
  return <MindmapElement title={block.title ?? "思维导图"} markdown={block.content ?? "# 占位思维导图"} />;
}
