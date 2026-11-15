from __future__ import annotations

import json
import os
import pickle
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_RAW_DIR = REPO_ROOT / "knowledge" / "raw"
KB_INDEX_DIR = REPO_ROOT / "storage" / "kb"
QDRANT_DIR = REPO_ROOT / "storage" / "qdrant_kb"


CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
EMBED_MODEL = "text-embedding-v3"
EMBED_DIM = 1024
EMBED_BATCH = 10

COLLECTION = "kb_chunks"
COLLECTION_BGE = "kb_chunks_bgem3"

BGE_MODEL_ENV = "BGE_M3_PATH"


def resolve_bge_model_path() -> Path:
    env = os.environ.get(BGE_MODEL_ENV, "").strip()
    candidates = [Path(env)] if env else []
    candidates += [
        REPO_ROOT / ".models" / "bge-m3",
        REPO_ROOT.parent.parent / ".models" / "bge-m3",
    ]
    for p in candidates:
        if (p / "config.json").exists():
            return p
    searched = ", ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        f"BGE-M3 model not found. Searched: {searched}. "
        "Download it first (ModelScope, no HF proxy needed): "
        "pip install modelscope && modelscope download --model BAAI/bge-m3 --local_dir .models/bge-m3"
    )


def _active_embedder_kind() -> str:
    return os.environ.get("KB_EMBEDDER", "bge_m3").strip().lower()


def _active_collection() -> str:
    bailian = _active_embedder_kind() == "bailian"
    return COLLECTION if bailian else COLLECTION_BGE


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    topic: str
    section: str
    text: str
    source_url: str = ""
    char_count: int = 0

    scope: str = "platform"

    source_refs: str = ""

    doc_offset: int = 0


_JUNK_SECTION_RE = re.compile(
    r"references|citations?|bibliography|参考文献|参考资料|引用文献|致谢|acknowledg(?:ement)?s?|"
    r"further reading|external links|see also",
    re.I,
)
_JUNK_LATEX_RE = re.compile(r"lxSVG@|pgfsys@|lx@inpgf", re.I)
_JUNK_NAV_HEADING = re.compile(r"^#{1,6}\s*(目录|contents|table of contents)\s*$", re.I)


def is_structural_junk(chunk: "Chunk") -> bool:
    """识别参考文献、目录及提取残留等结构垃圾。"""
    if _JUNK_SECTION_RE.search(chunk.section or ""):
        return True
    if _JUNK_LATEX_RE.search(chunk.text):
        return True
    lines = [ln for ln in chunk.text.splitlines() if ln.strip()]
    if lines:
        link = [
            ln
            for ln in lines
            if re.search(r"\[[^\]]*\]\(", ln) or re.match(r"^- \[[ x]\]", ln)
        ]
        if (
            link
            and len(link) / len(lines) > 0.6
            and sum(len(ln) for ln in link) / len(link) < 120
        ):
            return True
    if _JUNK_NAV_HEADING.match(
        chunk.text.strip().splitlines()[0] if chunk.text.strip() else ""
    ):
        return True
    return False


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """读取平面字段格式的文档头部。"""
    meta: dict[str, str] = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    meta[key.strip()] = value.strip().strip('"').strip("'")
            body = parts[2]
    return meta, body


def _split_long_text_spans(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> "list[tuple[str, int]]":
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be smaller than chunk_size ({chunk_size})"
        )
    if len(text) <= chunk_size:
        stripped = text.strip()
        return [(stripped, 0)] if stripped else []
    pieces: list[tuple[str, int]] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind("。"), window.rfind(". "), window.rfind("\n\n"))
            if cut > chunk_size // 2:
                end = start + cut + 1
        piece = text[start:end]
        stripped = piece.strip()
        if stripped:
            lead = len(piece) - len(piece.lstrip())
            pieces.append((stripped, start + lead))
        start = end - chunk_overlap if end < len(text) else end
    return pieces


def _chunk_body(
    doc_id: str,
    title: str,
    topic: str,
    source_url: str,
    scope: str,
    body: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:

    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\[(\d+)\]", "", body)
    chunks: list[Chunk] = []

    section_starts = [0]
    for m in re.finditer(r"\n(?=#{2,3}\s)", body):
        section_starts.append(m.end())
    section_ends = section_starts[1:] + [len(body)]
    for sec_start, sec_end in zip(section_starts, section_ends):
        sec = body[sec_start:sec_end]
        sec_lines = sec.strip().splitlines()
        if not sec_lines:
            continue
        sec_lead = len(sec) - len(sec.lstrip())
        if sec_lines[0].startswith("#"):
            section_title = sec_lines[0].lstrip("#").strip()
            joined = "\n".join(sec_lines[1:])

            heading_len = len(sec_lines[0]) + 1
        else:
            section_title = "intro"
            joined = "\n".join(sec_lines)
            heading_len = 0
        sec_text = joined.strip()
        if not sec_text:
            continue

        content_base = (
            sec_start + sec_lead + heading_len + (len(joined) - len(joined.lstrip()))
        )

        for idx, (piece, piece_off) in enumerate(
            _split_long_text_spans(sec_text, chunk_size, chunk_overlap)
        ):
            if len(piece) < 60:
                continue
            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}::{section_title}::{idx}",
                    doc_id=doc_id,
                    title=title,
                    topic=topic,
                    section=section_title,
                    text=piece,
                    source_url=source_url,
                    char_count=len(piece),
                    scope=scope,
                    doc_offset=content_base + piece_off,
                )
            )
    return chunks


def chunk_markdown(path: Path) -> list[Chunk]:
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    doc_id = path.stem
    return _chunk_body(
        doc_id=doc_id,
        title=meta.get("title") or doc_id,
        topic=meta.get("topic") or "general",
        source_url=meta.get("source_url") or "",
        scope=meta.get("scope") or "platform",
        body=body,
    )


def chunks_from_text(
    doc_id: str,
    title: str,
    text: str,
    topic: str = "general",
    source_url: str = "",
    scope: str = "attachment",
) -> list[Chunk]:
    """将任务材料按相同规则切分。"""
    return _chunk_body(
        doc_id=doc_id,
        title=title,
        topic=topic,
        source_url=source_url,
        scope=scope,
        body=text,
    )


def load_all_chunks(force_rebuild: bool = False) -> list[Chunk]:
    cache = KB_INDEX_DIR / "chunks.jsonl"
    if cache.exists() and not force_rebuild:
        chunks = []
        for line in cache.read_text(encoding="utf-8").splitlines():
            if line.strip():
                chunks.append(Chunk(**json.loads(line)))
        if chunks:
            return chunks
    chunks: list[Chunk] = []
    for md in sorted(KB_RAW_DIR.glob("*.md")):
        chunks.extend(chunk_markdown(md))
    KB_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        "\n".join(json.dumps(asdict(c), ensure_ascii=False) for c in chunks),
        encoding="utf-8",
    )
    return chunks


def tokenize(text: str) -> list[str]:
    import jieba

    tokens = jieba.lcut(text.lower())
    return [t for t in tokens if re.search(r"[\w\u4e00-\u9fd5]", t)]


class BM25Index:
    def __init__(self, chunks: list[Chunk]) -> None:
        from rank_bm25 import BM25Okapi

        self.chunks = chunks
        self.chunk_by_id = {c.chunk_id: c for c in chunks}
        self.doc_ids = [c.chunk_id for c in chunks]

        self.corpus_tokens = [
            tokenize(f"{c.title} {c.title} {c.section} {c.text}") for c in chunks
        ]
        self.bm25 = BM25Okapi(self.corpus_tokens) if self.corpus_tokens else None

    def search(
        self, query: str, top_k: int = 10, min_rel: float = 0.0
    ) -> list[tuple[Chunk, float]]:
        """统一的关键词、向量及融合检索入口。"""
        if self.bm25 is None:
            return []
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self.doc_ids, scores), key=lambda x: x[1], reverse=True)[
            :top_k
        ]
        best = ranked[0][1] if ranked and ranked[0][1] > 0 else 0.0
        threshold = best * min_rel
        return [
            (self.chunk_by_id[cid], float(score))
            for cid, score in ranked
            if score > 0 and score >= threshold
        ]

    def save(self) -> None:
        KB_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        with (KB_INDEX_DIR / "bm25.pkl").open("wb") as f:
            pickle.dump(
                {"doc_ids": self.doc_ids, "corpus_tokens": self.corpus_tokens}, f
            )


def load_bm25_index(
    chunks: list[Chunk] | None = None, force_rebuild: bool = False
) -> BM25Index:
    chunks = (
        chunks if chunks is not None else load_all_chunks(force_rebuild=force_rebuild)
    )
    return BM25Index(chunks)


class BailianEmbedder:
    def __init__(
        self, api_key: str | None = None, client: httpx.Client | None = None
    ) -> None:
        self.api_key = api_key or os.environ.get(
            "CONTENT_GENERATOR_BAILIAN_API_KEY", ""
        )
        if not self.api_key:
            raise ValueError("Bailian API key is required for local KB embeddings.")
        self.client = client or httpx.Client(timeout=60.0)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), EMBED_BATCH):
            batch = [t[:6000] for t in texts[start : start + EMBED_BATCH]]
            response = self.client.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": EMBED_MODEL, "input": batch, "dimensions": EMBED_DIM},
            )
            if response.status_code != 200:
                bad = batch[0][:80]
                raise RuntimeError(
                    f"Embedding batch {start} failed: HTTP {response.status_code}: {response.text[:200]} | first item: {bad!r}"
                )
            data = sorted(response.json()["data"], key=lambda item: item["index"])
            vectors.extend([item["embedding"] for item in data])
        return vectors


class Embedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class BGEM3Embedder:
    """按需加载本地 BGE-M3 模型。"""

    def __init__(
        self,
        model_path: str | Path | None = None,
        batch_size: int = 8,
        max_length: int = 2048,
    ) -> None:
        self.model_path = (
            str(model_path) if model_path else str(resolve_bge_model_path())
        )
        self.batch_size = batch_size
        self.max_length = max_length
        self._model: "object | None" = None

    def _load(self) -> None:
        try:
            import torch
            from FlagEmbedding import BGEM3FlagModel
        except ImportError as exc:
            raise RuntimeError(
                "BGE-M3 local embedding needs torch + FlagEmbedding: "
                "uv pip install torch FlagEmbedding"
            ) from exc
        use_fp16 = torch.cuda.is_available()
        print(f"loading BGE-M3 from {self.model_path} (fp16={use_fp16}) ...")
        self._model = BGEM3FlagModel(self.model_path, use_fp16=use_fp16)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._model is None:
            self._load()
        out: list[list[float]] = []
        chunk_size = self.batch_size * 8
        for start in range(0, len(texts), chunk_size):
            batch = texts[start : start + chunk_size]
            result = self._model.encode(
                batch,
                batch_size=self.batch_size,
                max_length=self.max_length,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False,
            )["dense_vecs"]
            out.extend(v.tolist() for v in result)
        return out


def get_embedder(kind: str | None = None, *, api_key: str | None = None) -> Embedder:
    """选择向量模型；独立调用时可显式传入服务凭据。"""
    kind = (kind or _active_embedder_kind()).lower()
    if kind == "bge_m3":
        return BGEM3Embedder()
    if kind == "bailian":
        return BailianEmbedder(api_key=api_key)
    raise ValueError(
        f"unknown embedder kind: {kind!r} (expected 'bge_m3' or 'bailian')"
    )


_QDRANT_CLIENT: "object | None" = None


def get_qdrant() -> "object":
    global _QDRANT_CLIENT
    if _QDRANT_CLIENT is None:
        from qdrant_client import QdrantClient

        _QDRANT_CLIENT = QdrantClient(path=str(QDRANT_DIR))
    return _QDRANT_CLIENT


def close_qdrant() -> None:
    """关闭本地向量存储并保存变更。"""
    global _QDRANT_CLIENT
    if _QDRANT_CLIENT is not None:
        try:
            _QDRANT_CLIENT.close()
        except Exception:
            pass
        _QDRANT_CLIENT = None


def chunk_point_id(chunk_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, chunk_id))


def ensure_vector_index(
    chunks: list[Chunk],
    embedder: Embedder,
    force_rebuild: bool = False,
    collection: str | None = None,
) -> None:
    from qdrant_client.models import Distance, PointStruct, VectorParams

    collection = collection or _active_collection()
    client = get_qdrant()
    existing = [c.name for c in client.get_collections().collections]
    if collection in existing and not force_rebuild:
        return
    if collection in existing:
        client.delete_collection(collection)
    client.create_collection(
        collection,
        vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
    )

    vectors = embedder.embed([f"{c.title} | {c.section} | {c.text}" for c in chunks])
    points = [
        PointStruct(
            id=chunk_point_id(c.chunk_id),
            vector=vec,
            payload={
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "title": c.title,
                "topic": c.topic,
                "scope": c.scope,
            },
        )
        for c, vec in zip(chunks, vectors)
    ]
    for start in range(0, len(points), 100):
        client.upsert(collection, points[start : start + 100])

    final = client.count(collection, exact=True).count
    if final != len(points):
        raise RuntimeError(
            f"vector index verification failed: collection {collection!r} has {final} points, expected {len(points)}. "
            "Run python -m knowledge.scripts.build_kb --rebuild."
        )


def search_vector(
    query: str,
    chunks: list[Chunk],
    embedder: Embedder,
    top_k: int = 10,
    collection: str | None = None,
    query_vector: "list[float] | None" = None,
) -> list[tuple[Chunk, float]]:
    collection = collection or _active_collection()
    client = get_qdrant()
    vec = query_vector if query_vector is not None else embedder.embed([query])[0]
    hits = client.query_points(collection, query=vec, limit=top_k).points
    chunk_by_id = {c.chunk_id: c for c in chunks}
    results = []
    for hit in hits:
        chunk = chunk_by_id.get(hit.payload.get("chunk_id"))
        if chunk:
            results.append((chunk, float(hit.score)))
    return results


def cosine_search(
    query: str,
    chunks: list[Chunk],
    embedder: Embedder,
    top_k: int = 10,
    vector_cache: "dict[str, list[list[float]]] | None" = None,
) -> list[tuple[Chunk, float]]:
    import hashlib

    import numpy as np

    texts = [f"{c.title} | {c.section} | {c.text}" for c in chunks]
    if vector_cache is not None:
        keys = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in texts]
        missing = [t for t, k in zip(texts, keys) if k not in vector_cache]
        if missing:
            for t, v in zip(missing, embedder.embed(missing)):
                vector_cache[hashlib.sha256(t.encode("utf-8")).hexdigest()] = v
        vectors = [vector_cache[k] for k in keys]
    else:
        vectors = embedder.embed(texts)

    qvec = np.array(embedder.embed([query])[0])
    mat = np.array(vectors)
    norms = np.linalg.norm(mat, axis=1) * np.linalg.norm(qvec)
    sims = mat @ qvec / (norms + 1e-9)
    ranked = sorted(zip(range(len(chunks)), sims), key=lambda x: x[1], reverse=True)[
        :top_k
    ]
    return [(chunks[i], float(s)) for i, s in ranked if s > 0.01]


def rrf_fuse(
    rankings: list[list[str]], k: int = 60, weights: list[float] | None = None
) -> dict[str, float]:
    """按各通道的排名进行加权融合。"""
    weights = weights or [1.0] * len(rankings)
    scores: dict[str, float] = {}
    for ranking, weight in zip(rankings, weights):
        for pos, cid in enumerate(ranking):
            scores[cid] = scores.get(cid, 0.0) + weight / (k + pos + 1)
    return scores


def classify_query(query: str) -> str:
    tokens = tokenize(query)
    if not tokens:
        return "semantic"
    english = sum(1 for t in tokens if re.fullmatch(r"[a-z0-9+#._\-]{2,}", t))
    return "term" if english / len(tokens) >= 0.35 else "semantic"


def search(
    method: str,
    query: str,
    chunks: list[Chunk],
    bm25: BM25Index,
    embedder: Embedder | None,
    top_k: int = 10,
) -> list[tuple[Chunk, float]]:
    """统一的关键词、向量及融合检索入口。"""
    if method == "keyword":
        return bm25.search(query, top_k=top_k)
    if embedder is None:
        raise ValueError("Vector retrieval requires a configured embedder.")
    if method == "vector":
        return search_vector(query, chunks, embedder, top_k=top_k)
    if method == "hybrid":
        kw = bm25.search(query, top_k=20, min_rel=0.35)
        vec = search_vector(query, chunks, embedder, top_k=20)
        fused = rrf_fuse([[c.chunk_id for c, _ in kw], [c.chunk_id for c, _ in vec]])
        chunk_by_id = {c.chunk_id: c for c in chunks}
        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            (chunk_by_id[cid], score) for cid, score in ranked if cid in chunk_by_id
        ]
    if method == "router":
        qtype = classify_query(query)
        weights = [1.5, 1.0] if qtype == "term" else [0.5, 1.0]
        kw = bm25.search(query, top_k=20, min_rel=0.35)
        vec = search_vector(query, chunks, embedder, top_k=20)
        fused = rrf_fuse(
            [[c.chunk_id for c, _ in kw], [c.chunk_id for c, _ in vec]],
            weights=weights,
        )
        chunk_by_id = {c.chunk_id: c for c in chunks}
        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            (chunk_by_id[cid], score) for cid, score in ranked if cid in chunk_by_id
        ]
    raise ValueError(f"Unknown retrieval method: {method}")
