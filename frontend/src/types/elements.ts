export interface BaseElement {
  id: string;
  type: string;
  title: string;
  metadata: Record<string, unknown>;
}

export interface TextElement extends BaseElement {
  type: "text";
  content: string;
  citations: string[];
}

export interface ImageElement extends BaseElement {
  type: "image";
  prompt: string;
  asset_url: string;
  alt_text: string;
}

export interface ChartElementSpec extends BaseElement {
  type: "chart";
  chart_type: "bar" | "line" | "pie";
  description?: string | null;
  x_axis: Record<string, unknown>;
  y_axis: Record<string, unknown>;
  series: Array<Record<string, unknown>>;
}

export interface MindmapElementSpec extends BaseElement {
  type: "mindmap";
  markdown: string;
}

export type ContentElement = TextElement | ImageElement | ChartElementSpec | MindmapElementSpec;
