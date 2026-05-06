import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.elements import ChartElement, ImageElement, MindmapElement, TextElement
from app.schemas.export import ExportRequest, ExportResult
from app.schemas.outline import Outline
from app.schemas.request import ContentGenerationRequest
from app.schemas.assets import AssetResponse
from app.schemas.specs import LectureSpec, SlideDeckSpec
from app.schemas.task import PreviewResponse, TaskResult


SCHEMA_MODELS = [
    ContentGenerationRequest,
    Outline,
    LectureSpec,
    SlideDeckSpec,
    TextElement,
    ImageElement,
    ChartElement,
    MindmapElement,
    PreviewResponse,
    TaskResult,
    ExportRequest,
    ExportResult,
    AssetResponse,
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
