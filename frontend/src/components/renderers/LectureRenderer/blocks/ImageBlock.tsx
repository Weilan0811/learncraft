import type { RenderBlock } from "../../../../types/lecture";
import { ImageElement } from "../../../elements/ImageElement";

interface ImageBlockProps {
  block: RenderBlock;
}

export function ImageBlock({ block }: ImageBlockProps) {
  return <ImageElement title={block.title ?? "图片"} assetUrl={block.asset_url} altText={block.title ?? "图片占位"} />;
}
