from typing import Any, Literal

from pydantic import Field

from app.schemas.base import SchemaModel


class SocialPostExportFile(SchemaModel):
    file_type: Literal["html", "json", "markdown", "image", "zip"]
    path: str
    url: str | None = None
    label: str | None = None


class SocialPostPreviewAsset(SchemaModel):
    slot_id: str
    caption: str
    local_path: str | None = None
    public_url: str | None = None
    wechat_url: str | None = None


class SocialPostRenderModel(SchemaModel):
    render_type: Literal["social_post"] = "social_post"
    content_type: Literal["social_post"] = "social_post"
    platform: Literal["wechat"] = "wechat"
    subtype: Literal["wechat_article"] = "wechat_article"
    title: str
    digest: str
    template: str
    html: str
    article_json: dict[str, Any]
    preview_assets: list[SocialPostPreviewAsset] = Field(default_factory=list)
    export_files: list[SocialPostExportFile] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
