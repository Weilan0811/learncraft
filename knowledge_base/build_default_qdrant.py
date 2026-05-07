"""Build the local default Qdrant knowledge base from Markdown files."""

from __future__ import annotations

import argparse
import re
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore

from app.core.config import Settings
from app.services.rag_service import BailianEmbeddingService

DEFAULT_RAW_DIR = REPO_ROOT / "knowledge_base" / "default" / "raw"
DEFAULT_QDRANT_PATH = REPO_ROOT / "storage" / "qdrant_data"
DEFAULT_COLLECTION = "default"
DEFAULT_CHUNK_SIZE = 1400
DEFAULT_CHUNK_OVERLAP = 200


class BailianDocumentEmbeddingService(BailianEmbeddingService, Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]


def discover_markdown_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw knowledge directory does not exist: {raw_dir}")
    files = sorted(path for path in raw_dir.glob("*.md") if path.is_file())
    if not files:
        raise FileNotFoundError(f"No Markdown files found in raw knowledge directory: {raw_dir}")
    return files


def split_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> list[str]:
    normalized = "\n\n".join(part.strip() for part in text.replace("\r\n", "\n").split("\n\n") if part.strip())
    if not normalized:
        return []
    if len(normalized) <= chunk_size:
        return [normalized]

    words = normalized.split()
    chunks: list[str] = []
    current_words: list[str] = []
    current_size = 0

    for word in words:
        separator_size = 1 if current_words else 0
        if current_words and current_size + separator_size + len(word) > chunk_size:
            chunk = " ".join(current_words)
            chunks.append(chunk)
            overlap_words = _overlap_words(current_words, chunk_overlap)
            current_words = overlap_words[:]
            current_size = len(" ".join(current_words))
        current_words.append(word)
        current_size += (1 if current_size else 0) + len(word)

    if current_words:
        chunk = " ".join(current_words)
        if not chunks or chunk != chunks[-1]:
            chunks.append(chunk)

    return chunks


def build_documents(
    markdown_files: list[Path],
    raw_dir: Path,
    collection_name: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    documents: list[Document] = []
    for source_path in markdown_files:
        text = source_path.read_text(encoding="utf-8")
        source_id = _slugify(source_path.stem)
        source_title = _extract_title(text) or source_path.stem
        relative_path = source_path.relative_to(raw_dir).as_posix()
        chunks = split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        for index, chunk in enumerate(chunks, start=1):
            chunk_id = f"{source_id}__chunk_{index:04d}"
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "id": chunk_id,
                        "chunk_id": chunk_id,
                        "source_id": source_id,
                        "document_id": source_id,
                        "source_title": source_title,
                        "title": source_title,
                        "source_path": relative_path,
                        "collection": collection_name,
                        "chunk_index": index,
                    },
                )
            )

    if not documents:
        raise ValueError("No knowledge chunks were created from Markdown sources.")
    return documents


def build_qdrant_collection(
    documents: list[Document],
    qdrant_path: Path,
    collection_name: str,
    embedding_service: BailianDocumentEmbeddingService,
    force: bool = False,
    batch_size: int = 16,
) -> None:
    qdrant_path.parent.mkdir(parents=True, exist_ok=True)
    QdrantVectorStore.from_documents(
        documents=documents,
        embedding=embedding_service,
        ids=[point_id_for_chunk_id(str(document.metadata["id"])) for document in documents],
        collection_name=collection_name,
        path=str(qdrant_path),
        batch_size=batch_size,
        force_recreate=force,
    )


def point_id_for_chunk_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"content-generator-agent:{chunk_id}"))


def resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the default local Qdrant knowledge base.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR, help="Directory containing source Markdown files.")
    parser.add_argument("--qdrant-path", type=Path, default=None, help="Local Qdrant data directory.")
    parser.add_argument("--collection", default=None, help="Qdrant collection name.")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help="Maximum characters per chunk.")
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP, help="Approximate overlap characters.")
    parser.add_argument("--batch-size", type=int, default=16, help="Qdrant insert batch size.")
    parser.add_argument("--force", action="store_true", help="Recreate the collection if it already exists.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings()
    if not settings.bailian_api_key:
        raise ValueError("CONTENT_GENERATOR_BAILIAN_API_KEY is required to build the Qdrant knowledge base.")

    collection_name = args.collection or settings.qdrant_collection or DEFAULT_COLLECTION
    qdrant_path = resolve_repo_path(args.qdrant_path or Path(settings.qdrant_path or DEFAULT_QDRANT_PATH))
    raw_dir = resolve_repo_path(args.raw_dir)

    markdown_files = discover_markdown_files(raw_dir)
    documents = build_documents(
        markdown_files,
        raw_dir=raw_dir,
        collection_name=collection_name,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    embedding_service = BailianDocumentEmbeddingService(
        api_key=settings.bailian_api_key,
        model=settings.embedding_model,
        base_url=settings.bailian_base_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    build_qdrant_collection(
        documents=documents,
        qdrant_path=qdrant_path,
        collection_name=collection_name,
        embedding_service=embedding_service,
        force=args.force,
        batch_size=args.batch_size,
    )
    print(f"Built Qdrant collection '{collection_name}' with {len(documents)} chunks at {qdrant_path}.")


def _overlap_words(words: list[str], chunk_overlap: int) -> list[str]:
    if chunk_overlap <= 0:
        return []
    overlap: list[str] = []
    size = 0
    for word in reversed(words):
        next_size = size + (1 if overlap else 0) + len(word)
        if overlap and next_size > chunk_overlap:
            break
        overlap.insert(0, word)
        size = len(" ".join(overlap))
    return overlap


def _extract_title(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or None
    return None


def _slugify(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z]+", "_", value.strip().lower()).strip("_")
    return slug or "document"


if __name__ == "__main__":
    main()
