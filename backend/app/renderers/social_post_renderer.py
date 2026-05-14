import re
from copy import deepcopy
from typing import Any

from app.schemas.elements import ContentElement
from app.schemas.render.social_post import SocialPostPreviewAsset, SocialPostRenderModel
from app.schemas.specs import ImageAsset, ImageSlot, SocialPostSpec
from app.services.wechat_claw_renderer import WechatClawRenderer


class SocialPostRenderer:
    def __init__(self, wechat_renderer: WechatClawRenderer | None = None) -> None:
        self.wechat_renderer = wechat_renderer or WechatClawRenderer()

    def render(self, spec: SocialPostSpec, elements: list[ContentElement]) -> SocialPostRenderModel:
        article_json = to_wechat_claw_article(spec)
        render_model = self.wechat_renderer.render(task_id=spec.id, article_json=article_json, check=True)
        return render_model.model_copy(
            update={
                "preview_assets": _preview_assets(spec),
                "warnings": [*render_model.warnings, *_asset_warnings(spec)],
            }
        )


def to_wechat_claw_article(spec: SocialPostSpec) -> dict[str, Any]:
    draft = spec.draft.model_dump(mode="json")
    article = {
        "template": draft["template"],
        "meta": draft["meta"],
        "headline": draft["headline"],
        "sections": draft["sections"],
        "conclusion": draft.get("conclusion"),
        "cta": draft.get("cta"),
    }
    bind_images(article, spec.image_slots, {asset.slot_id: asset for asset in spec.image_assets})
    strip_internal_fields(article)
    return article


def bind_images(article: dict[str, Any], image_slots: list[ImageSlot], assets_by_slot: dict[str, ImageAsset]) -> None:
    for slot in image_slots:
        asset = assets_by_slot.get(slot.slot_id)
        if asset is None or asset.status != "generated":
            continue
        url = asset.wechat_url or asset.public_url or asset.local_path
        if not url:
            continue
        image_payload = {
            "slot_id": slot.slot_id,
            "url": url,
            "local_path": asset.local_path,
            "caption": slot.caption,
            "prompt": slot.prompt_en,
        }
        if slot.target_path == "meta.cover_image":
            article.setdefault("meta", {})["cover_image"] = deepcopy(image_payload)
            if asset.media_id:
                article["meta"]["thumb_media_id"] = asset.media_id
        elif slot.target_path == "headline.image":
            article.setdefault("headline", {})["image"] = deepcopy(image_payload)
        else:
            match = re.fullmatch(r"sections\[(\d+)\]\.image", slot.target_path)
            if match:
                index = int(match.group(1))
                sections = article.get("sections") or []
                if 0 <= index < len(sections):
                    sections[index]["image"] = deepcopy(image_payload)


def strip_internal_fields(obj: object) -> None:
    if isinstance(obj, dict):
        for key in ["section_id", "citation_refs", "slot_id", "writing_notes", "estimated_word_count"]:
            obj.pop(key, None)
        for value in obj.values():
            strip_internal_fields(value)
    elif isinstance(obj, list):
        for item in obj:
            strip_internal_fields(item)


def _preview_assets(spec: SocialPostSpec) -> list[SocialPostPreviewAsset]:
    assets = {asset.slot_id: asset for asset in spec.image_assets}
    preview_assets: list[SocialPostPreviewAsset] = []
    for slot in spec.image_slots:
        asset = assets.get(slot.slot_id)
        preview_assets.append(
            SocialPostPreviewAsset(
                slot_id=slot.slot_id,
                caption=slot.caption,
                local_path=asset.local_path if asset else None,
                public_url=asset.public_url if asset else None,
                wechat_url=asset.wechat_url if asset else None,
            )
        )
    return preview_assets


def _asset_warnings(spec: SocialPostSpec) -> list[str]:
    return [f"image slot {asset.slot_id} failed: {asset.error_message}" for asset in spec.image_assets if asset.status == "failed"]
