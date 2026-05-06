export interface RenderBlock {
  id: string;
  type: string;
  title?: string | null;
  content?: string | null;
  asset_url?: string | null;
  metadata: Record<string, unknown>;
}

export interface LectureRenderSection {
  id: string;
  title: string;
  render_blocks: RenderBlock[];
}

export interface LectureRenderModel {
  render_type: "lecture_page";
  title: string;
  objectives: string[];
  sections: LectureRenderSection[];
  printable_model: Record<string, unknown>;
}
