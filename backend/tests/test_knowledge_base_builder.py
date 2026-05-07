from pathlib import Path
import importlib.util

import pytest
from langchain_core.embeddings import Embeddings

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "knowledge_base" / "build_default_qdrant.py"
spec = importlib.util.spec_from_file_location("build_default_qdrant", SCRIPT_PATH)
assert spec is not None
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(builder)

build_documents = builder.build_documents
build_qdrant_collection = builder.build_qdrant_collection
BailianDocumentEmbeddingService = builder.BailianDocumentEmbeddingService
discover_markdown_files = builder.discover_markdown_files
point_id_for_chunk_id = builder.point_id_for_chunk_id
resolve_repo_path = builder.resolve_repo_path
split_text = builder.split_text


def test_discover_markdown_files_returns_sorted_markdown_only(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "b.md").write_text("# B\n\ncontent", encoding="utf-8")
    (raw_dir / "a.md").write_text("# A\n\ncontent", encoding="utf-8")
    (raw_dir / "notes.txt").write_text("ignored", encoding="utf-8")

    files = discover_markdown_files(raw_dir)

    assert [file.name for file in files] == ["a.md", "b.md"]


def test_discover_markdown_files_rejects_empty_directory(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="No Markdown files"):
        discover_markdown_files(raw_dir)


def test_split_text_keeps_overlap_between_chunks() -> None:
    text = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"

    chunks = split_text(text, chunk_size=25, chunk_overlap=12)

    assert len(chunks) > 1
    assert chunks[0].endswith("delta")
    assert chunks[1].startswith("gamma")


def test_build_documents_preserves_source_metadata(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    source = raw_dir / "lesson.md"
    source.write_text("# Lesson Title\n\nFirst paragraph.\n\nSecond paragraph.", encoding="utf-8")

    documents = build_documents([source], raw_dir=raw_dir, collection_name="default", chunk_size=80, chunk_overlap=20)

    assert len(documents) == 1
    document = documents[0]
    assert document.page_content.startswith("# Lesson Title")
    assert document.metadata["id"] == "lesson__chunk_0001"
    assert document.metadata["chunk_id"] == "lesson__chunk_0001"
    assert document.metadata["source_id"] == "lesson"
    assert document.metadata["source_title"] == "Lesson Title"
    assert document.metadata["collection"] == "default"
    assert document.metadata["source_path"] == "lesson.md"
    assert document.metadata["chunk_index"] == 1


def test_resolve_repo_path_expands_relative_paths_from_repo_root() -> None:
    path = resolve_repo_path(Path("storage/qdrant_data"))

    assert path == SCRIPT_PATH.parents[1] / "storage" / "qdrant_data"


def test_point_id_for_chunk_id_returns_stable_uuid() -> None:
    point_id = point_id_for_chunk_id("a_framework_for_ai_literacy__chunk_0001")

    assert point_id == point_id_for_chunk_id("a_framework_for_ai_literacy__chunk_0001")
    assert point_id != point_id_for_chunk_id("a_framework_for_ai_literacy__chunk_0002")
    assert len(point_id) == 36


def test_bailian_document_embedding_service_satisfies_langchain_embedding_type() -> None:
    assert issubclass(BailianDocumentEmbeddingService, Embeddings)


def test_build_qdrant_collection_uses_valid_point_ids(tmp_path: Path) -> None:
    class FakeEmbeddings(Embeddings):
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [[float(len(text)), 1.0] for text in texts]

        def embed_query(self, text: str) -> list[float]:
            return [float(len(text)), 1.0]

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    source = raw_dir / "lesson.md"
    source.write_text("# Lesson\n\nA small chunk about retrieval.", encoding="utf-8")
    documents = build_documents([source], raw_dir=raw_dir, collection_name="default")
    qdrant_path = tmp_path / "qdrant_data"

    build_qdrant_collection(
        documents=documents,
        qdrant_path=qdrant_path,
        collection_name="default",
        embedding_service=FakeEmbeddings(),
        force=True,
    )

    assert (qdrant_path / "collection" / "default").exists()
