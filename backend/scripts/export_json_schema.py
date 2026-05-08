import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.request import ContentGenerationRequest, GenerationOptions
from app.schemas.outline import Outline, OutlineSection, OutlineUnit
from app.schemas.specs import LectureSpec, LectureSection, SlideDeckSpec, SlideSpecPage, TextBlock, ElementReferenceBlock
from app.schemas.elements import ContentElement, ImageElement, MindmapElement
from app.schemas.render import LectureRenderModel, SlideRenderModel, RenderBlock



SCHEMA_MODELS = [
    ContentGenerationRequest,
    GenerationOptions,
    Outline,
    OutlineSection,
    OutlineUnit,
    LectureSpec,
    LectureSection,
    SlideDeckSpec,
    SlideSpecPage,
    TextBlock,
    ElementReferenceBlock,
    ImageElement,
    MindmapElement,
    LectureRenderModel,
    SlideRenderModel,
    RenderBlock
]


def main() -> None:
    output_dir = BACKEND_DIR / "schema_exports"
    output_dir.mkdir(exist_ok=True)
    for model in SCHEMA_MODELS:
        path = output_dir / f"{model.__name__}.schema.json"
        path.write_text(
            json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
