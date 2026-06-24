import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import cast

from app.core.fallback import allow_generation_fallback
from app.core.config import get_settings
from app.schemas.elements import ImageElement
from app.schemas.specs import (
    CardBlock,
    CitationRef,
    ImageAsset,
    ImageSlot,
    ImageSlotPlan,
    ParagraphBlock,
    SocialPostSpec,
    WechatArticleDraft,
    WechatBriefOutline,
    WechatHeadline,
    WechatMeta,
    WechatOutlineSection,
    WechatSection,
)
from app.schemas.state import ContentGenerationState, RetrievedChunk
from app.services.image_generation_service import get_image_generation_service
from app.services.llm_service import get_llm_service


class SocialPostGenerationError(RuntimeError):
    def __init__(self, stage: str, original: Exception) -> None:
        super().__init__(f"{stage} failed: {original}")
        self.stage = stage
        self.original = original


class SocialPostGenerator:
    def generate(self, state: ContentGenerationState) -> SocialPostSpec:
        settings = get_settings()
        if settings.provider_mode != "stub":
            try:
                spec = self._generate_with_llm(state)
            except Exception as exc:
                if not allow_generation_fallback(state, provider_mode=settings.provider_mode):
                    raise
                spec = self._generate_fallback(state)
                spec = spec.model_copy(
                    update={
                        "metadata": {
                            **spec.metadata,
                            "generation_mode": "fallback",
                            "fallback_reason": str(exc),
                        }
                    }
                )
        else:
            spec = self._generate_fallback(state)
            spec = spec.model_copy(update={"metadata": {**spec.metadata, "generation_mode": "stub_fallback"}})
        spec = self._normalize_citation_refs(state, spec)
        return self._generate_image_assets(state, spec)

    def _generate_with_llm(self, state: ContentGenerationState) -> SocialPostSpec:
        llm_service = get_llm_service()
        outline_prompt = self._prompt("planner", "social_post_outline.md", state)
        try:
            outline = cast(WechatBriefOutline, llm_service.generate_structured(outline_prompt, WechatBriefOutline))
        except Exception as exc:
            raise SocialPostGenerationError("social_post_outline_generation", exc) from exc
        draft_prompt = self._prompt("generator", "social_post_draft.md", state, outline=outline.model_dump(mode="json"))
        try:
            draft = cast(WechatArticleDraft, llm_service.generate_structured(draft_prompt, WechatArticleDraft))
        except Exception as exc:
            raise SocialPostGenerationError("social_post_draft_generation", exc) from exc
        image_prompt = self._prompt("generator", "social_post_image.md", state, draft=draft.model_dump(mode="json"))
        try:
            slot_plan = cast(ImageSlotPlan, llm_service.generate_structured(image_prompt, ImageSlotPlan))
        except Exception as exc:
            raise SocialPostGenerationError("social_post_image_plan_generation", exc) from exc
        return SocialPostSpec(
            id=f"social_{state.request_id}",
            title=draft.meta.title,
            metadata={"language": (state.normalized_request or {}).get("language", "zh-CN"), "generation_mode": "llm"},
            outline=outline,
            draft=draft,
            image_slots=slot_plan.image_slots,
        )

    def _generate_fallback(self, state: ContentGenerationState) -> SocialPostSpec:
        chunks = state.planning_chunks or state.retrieved_chunks
        refs = self._citation_refs(chunks)
        topic = state.topic.strip()
        safe_title = _truncate(topic or "Social post", 28)
        digest = _truncate(f"A structured WeChat article about {topic}, generated through the direct workflow.", 120)
        sections = [
            WechatOutlineSection(
                section_id="sec-01",
                title="Why this matters",
                core_question=f"What problem does {topic} help readers understand?",
                key_points=["Start from the reader's practical question.", "Explain the context before the method."],
                evidence_refs=refs,
                suggested_visual="concept diagram",
            ),
            WechatOutlineSection(
                section_id="sec-02",
                title="How the workflow works",
                core_question="How do the main parts connect?",
                key_points=["Keep article generation as one coherent artifact.", "Reuse retrieval, storage, and preview snapshots."],
                evidence_refs=refs,
                suggested_visual="workflow diagram",
            ),
            WechatOutlineSection(
                section_id="sec-03",
                title="What to validate",
                core_question="Which checks make the output dependable?",
                key_points=["Validate text structure first.", "Bind assets before final HTML rendering."],
                evidence_refs=refs,
                suggested_visual="checklist diagram",
            ),
        ]
        outline = WechatBriefOutline(
            topic=topic,
            article_type="engineering_practice",
            writing_angle="Use a practical engineering explanation instead of a broad overview.",
            core_question=f"How should readers understand {topic}?",
            central_thesis="A direct workflow keeps social-post generation compact while sharing backend infrastructure.",
            reader_question_chain=[
                "What is the concrete problem?",
                "How is the workflow organized?",
                "What needs validation before preview?",
            ],
            title_candidates=[safe_title],
            recommended_template="deep-analysis",
            sections=sections,
        )
        draft_sections = [
            WechatSection(
                section_id=section.section_id,
                cn=section.title,
                en=f"PART {index:02d}",
                intro=section.core_question,
                blocks=[
                    ParagraphBlock(
                        text=(
                            f"{section.core_question} The useful answer is not to add more branches to the main graph, "
                            "but to keep this article path direct and observable."
                        ),
                        citation_refs=refs,
                    ),
                    CardBlock(
                        number=index,
                        title=section.key_points[0],
                        body=section.key_points,
                        source=refs[0].title if refs else None,
                        citation_refs=refs,
                    ),
                ],
                citation_refs=refs,
            )
            for index, section in enumerate(sections, 1)
        ]
        draft = WechatArticleDraft(
            template=outline.recommended_template,
            meta=WechatMeta(title=safe_title, digest=digest),
            headline=WechatHeadline(
                title=safe_title,
                body=[
                    f"This article turns {topic} into a concrete backend generation path.",
                    "The key is to keep the direct article path small while sharing existing services.",
                ],
                citation_refs=refs,
            ),
            sections=draft_sections,
            conclusion="The direct workflow gives social posts a stable backend path without expanding the unit-loop graph.",
            cta="Use this preview as the starting point for editorial review.",
        )
        slots = [
            ImageSlot(
                slot_id="cover",
                target="meta.cover_image",
                target_path="meta.cover_image",
                aspect_ratio="2.35:1",
                caption=f"{safe_title} cover",
                visual_type="cover",
                purpose="Set the article theme in the WeChat preview.",
                context_summary=draft.headline.body[0],
                prompt_en=f"Professional WeChat article cover about {topic}, clean technology editorial style, wide composition.",
            ),
            ImageSlot(
                slot_id="headline",
                target="headline.image",
                target_path="headline.image",
                aspect_ratio="16:9",
                caption="Direct workflow overview",
                visual_type="workflow_diagram",
                purpose="Explain the article workflow before the main sections.",
                context_summary=draft.headline.body[1],
                prompt_en=f"Clear workflow diagram for {topic}, backend direct path, professional technical article style.",
            ),
            ImageSlot(
                slot_id="sec-01",
                target="section.image",
                target_path="sections[0].image",
                required=False,
                aspect_ratio="16:9",
                caption="Article structure",
                visual_type="concept_diagram",
                purpose="Support the first section with a simple conceptual visual.",
                context_summary=draft_sections[0].intro or draft_sections[0].cn,
                prompt_en=f"Concept diagram showing why direct workflow helps with {topic}, clean labels, no logos.",
            ),
        ]
        return SocialPostSpec(
            id=f"social_{state.request_id}",
            title=safe_title,
            metadata={"language": (state.normalized_request or {}).get("language", "zh-CN")},
            outline=outline,
            draft=draft,
            image_slots=slots,
        )

    def _generate_image_assets(self, state: ContentGenerationState, spec: SocialPostSpec) -> SocialPostSpec:
        if not bool((state.normalized_request or {}).get("include_images", True)):
            return spec
        service = get_image_generation_service()
        if not spec.image_slots:
            return spec
        settings = get_settings()
        configured_concurrency = int(getattr(settings, "image_generation_concurrency", 3))
        max_workers = max(1, min(configured_concurrency, len(spec.image_slots)))
        assets_by_index: dict[int, ImageAsset] = {}

        def generate_slot(index: int, slot: ImageSlot) -> tuple[int, ImageAsset]:
            try:
                image = service.generate_image(
                    title=slot.caption,
                    description=slot.prompt_en,
                    aspect_ratio=self._provider_aspect_ratio(slot.aspect_ratio),
                    asset_id=f"social_{state.request_id}_{slot.slot_id}",
                )
                return index, _asset_from_image(slot.slot_id, image)
            except Exception as exc:
                return index, ImageAsset(slot_id=slot.slot_id, status="failed", error_message=str(exc))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(generate_slot, index, slot) for index, slot in enumerate(spec.image_slots)]
            for future in as_completed(futures):
                index, asset = future.result()
                assets_by_index[index] = asset
        assets = [assets_by_index[index] for index in range(len(spec.image_slots))]
        return spec.model_copy(update={"image_assets": assets})

    def _normalize_citation_refs(self, state: ContentGenerationState, spec: SocialPostSpec) -> SocialPostSpec:
        refs = self._citation_refs(state.planning_chunks or state.retrieved_chunks)
        draft = spec.draft.model_copy(deep=True)
        if not draft.headline.citation_refs:
            draft.headline.citation_refs = refs
        for section in draft.sections:
            if not section.citation_refs:
                section.citation_refs = refs
            for block in section.blocks:
                if hasattr(block, "citation_refs") and not block.citation_refs:
                    block.citation_refs = refs
        outline = spec.outline.model_copy(deep=True)
        for section in outline.sections:
            if not section.evidence_refs:
                section.evidence_refs = refs
        return spec.model_copy(update={"draft": draft, "outline": outline})

    @staticmethod
    def _provider_aspect_ratio(aspect_ratio: str) -> str:
        if aspect_ratio == "2.35:1":
            return "21:9"
        return aspect_ratio

    @staticmethod
    def _citation_refs(chunks: list[RetrievedChunk]) -> list[CitationRef]:
        if not chunks:
            return [CitationRef(chunk_id="stub_chunk", title="Generated fallback source", note="Fallback source for local testing.")]
        return [
            CitationRef(
                chunk_id=chunk.id,
                source_id=chunk.source_id,
                title=chunk.source_title,
                note=_truncate(chunk.content, 80),
            )
            for chunk in chunks[:2]
        ]

    @staticmethod
    def _prompt(group: str, filename: str, state: ContentGenerationState, **payload: object) -> str:
        path = os.path.join(os.path.dirname(__file__), "..", "prompts", group, filename)
        template = open(path, "r", encoding="utf-8").read()
        data = {
            "user_request": json.dumps(state.raw_request or {}, ensure_ascii=False, indent=2),
            "generation_options": json.dumps(state.normalized_request or {}, ensure_ascii=False, indent=2),
            "retrieved_chunks": json.dumps([chunk.model_dump(mode="json") for chunk in state.planning_chunks], ensure_ascii=False, indent=2),
            **payload,
        }
        return template.format(**data)


def _asset_from_image(slot_id: str, image: ImageElement) -> ImageAsset:
    return ImageAsset(
        slot_id=slot_id,
        status="generated",
        local_path=image.asset_url,
        public_url=image.asset_url,
        width=image.width if isinstance(image.width, int) else None,
        height=image.height if isinstance(image.height, int) else None,
    )


def _truncate(value: str, length: int) -> str:
    value = " ".join(value.split())
    return value if len(value) <= length else value[: length - 1].rstrip() + "…"
