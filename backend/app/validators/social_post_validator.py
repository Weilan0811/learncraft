import re

from app.schemas.specs import ImageSlot, SocialPostSpec, SocialPostValidationIssue, SocialPostValidationReport


class SocialPostValidator:
    def validate_pre_assets(self, spec: SocialPostSpec, available_chunk_ids: set[str] | None = None) -> SocialPostValidationReport:
        issues: list[SocialPostValidationIssue] = []
        available_chunk_ids = available_chunk_ids or set()
        if not spec.draft.meta.title:
            issues.append(_error("draft.meta.title", "meta.title is required"))
        if len(spec.draft.meta.title) > 32:
            issues.append(_error("draft.meta.title", "meta.title must be <= 32 characters"))
        if not spec.draft.meta.digest:
            issues.append(_error("draft.meta.digest", "meta.digest is required"))
        if len(spec.draft.meta.digest) > 128:
            issues.append(_error("draft.meta.digest", "meta.digest must be <= 128 characters"))
        if not spec.draft.headline.body:
            issues.append(_error("draft.headline.body", "headline.body is required"))
        if not 3 <= len(spec.draft.sections) <= 7:
            issues.append(_error("draft.sections", "sections must contain 3 to 7 items"))
        for index, section in enumerate(spec.draft.sections):
            if not section.blocks:
                issues.append(_error(f"draft.sections[{index}].blocks", "section must have at least one block"))
            if not section.citation_refs:
                issues.append(_error(f"draft.sections[{index}].citation_refs", "section must include citation_refs"))
            for ref in section.citation_refs:
                if available_chunk_ids and ref.chunk_id not in available_chunk_ids:
                    issues.append(_error(f"draft.sections[{index}].citation_refs", f"unknown chunk_id: {ref.chunk_id}"))
        slot_ids = [slot.slot_id for slot in spec.image_slots]
        if len(slot_ids) != len(set(slot_ids)):
            issues.append(_error("image_slots", "image slot ids must be unique"))
        if spec.image_slots and not any(slot.slot_id == "cover" and slot.target_path == "meta.cover_image" for slot in spec.image_slots):
            # Cover is only mandatory when the task actually plans images; legacy
            # specs generated before the fixed image policy may have no slots.
            issues.append(_error("image_slots", "image_slots must include a cover slot"))
        for index, slot in enumerate(spec.image_slots):
            issues.extend(self._validate_slot(slot, index, len(spec.draft.sections)))
        return SocialPostValidationReport(ok=not any(issue.severity == "error" for issue in issues), issues=issues)

    def validate_final(self, spec: SocialPostSpec, html: str | None = None) -> SocialPostValidationReport:
        issues = list((spec.validation_report.issues if spec.validation_report else []))
        assets_by_slot = {asset.slot_id: asset for asset in spec.image_assets}
        for slot in spec.image_slots:
            asset = assets_by_slot.get(slot.slot_id)
            if slot.required and (asset is None or asset.status != "generated" or not (asset.wechat_url or asset.public_url or asset.local_path)):
                issues.append(_error(f"image_assets.{slot.slot_id}", f"required image slot {slot.slot_id} is missing a generated asset"))
        if spec.article_json is None:
            issues.append(_error("article_json", "article_json is required"))
        if html is not None:
            if not html.strip():
                issues.append(_error("html", "rendered HTML is empty"))
            if "{{" in html or "}}" in html:
                issues.append(_error("html", "rendered HTML still contains unresolved placeholders"))
            if len(html.encode("utf-8")) > 1024 * 1024:
                issues.append(_error("html", "rendered HTML exceeds 1MB"))
        return SocialPostValidationReport(ok=not any(issue.severity == "error" for issue in issues), issues=issues)

    @staticmethod
    def _validate_slot(slot: ImageSlot, index: int, section_count: int) -> list[SocialPostValidationIssue]:
        issues: list[SocialPostValidationIssue] = []
        if not slot.prompt_en.strip():
            issues.append(_error(f"image_slots[{index}].prompt_en", "prompt_en is required"))
        if slot.target_path == "meta.cover_image":
            if slot.aspect_ratio != "2.35:1":
                issues.append(_error(f"image_slots[{index}].aspect_ratio", "cover slot must use 2.35:1"))
            return issues
        if slot.target_path == "headline.image":
            return issues
        match = re.fullmatch(r"sections\[(\d+)\]\.image", slot.target_path)
        if match:
            section_index = int(match.group(1))
            if section_index >= section_count:
                issues.append(_error(f"image_slots[{index}].target_path", f"target_path references missing section: {slot.target_path}"))
            return issues
        issues.append(_error(f"image_slots[{index}].target_path", f"unsupported target_path: {slot.target_path}"))
        return issues


def _error(path: str, message: str) -> SocialPostValidationIssue:
    return SocialPostValidationIssue(severity="error", path=path, message=message)
