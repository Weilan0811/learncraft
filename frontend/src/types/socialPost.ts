export interface SocialPostExportFile {
  file_type: "html" | "json" | "markdown" | "image" | "zip";
  path: string;
  url?: string | null;
  label?: string | null;
}

export interface SocialPostPreviewAsset {
  slot_id: string;
  caption: string;
  local_path?: string | null;
  public_url?: string | null;
  wechat_url?: string | null;
}

export interface SocialPostRenderModel {
  render_type: "social_post";
  content_type: "social_post";
  platform: "wechat";
  subtype: "wechat_article";
  title: string;
  digest: string;
  template: string;
  html: string;
  article_json: Record<string, unknown>;
  preview_assets: SocialPostPreviewAsset[];
  export_files: SocialPostExportFile[];
  warnings: string[];
}
