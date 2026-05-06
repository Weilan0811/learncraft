export interface SlidePageModel {
  version: "scenekit.slide/v1";
  page: Record<string, unknown>;
}

export interface SlideRenderModel {
  render_type: "slide_deck";
  title: string;
  pages: SlidePageModel[];
}
