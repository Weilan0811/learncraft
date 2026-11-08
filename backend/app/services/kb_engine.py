"""Local knowledge-base engine shared by the generation pipeline and eval scripts.

Chunks markdown documents from ``knowledge/raw/``, builds a BM25 index
(jieba tokens) plus a Qdrant local dense index (Bailian text-embedding), and
exposes the four retrieval strategies compared in the D2 evaluation:

- ``keyword``  : BM25 over jieba tokens (baseline, mimics the lab keyword API)
- ``vector``   : dense retrieval only
- ``hybrid``   : BM25 + dense fused with reciprocal rank fusion (RRF)
- ``router``   : index-based topic routing, then hybrid inside the topic

Indexes under ``storage/kb`` and ``storage/qdrant_kb`` are derivable artifacts:
they can be rebuilt at any time from ``knowledge/raw/`` via
``knowledge/scripts/build_kb.py``.
"""

from __future__ import annotations

import json
import math
import os
import pickle
import re
import warnings
from dataclasses import dataclass, asdict
from pathlib import Path

warnings.filterwarnings("ignore")

import httpx

REPO_ROOT = Path(__file__).resolve().parents[3]
KB_RAW_DIR = REPO_ROOT / "knowledge" / "raw"
KB_INDEX_DIR = REPO_ROOT / "storage" / "kb"
QDRANT_DIR = REPO_ROOT / "storage" / "qdrant_kb"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
EMBED_MODEL = "text-embedding-v3"
EMBED_DIM = 1024
EMBED_BATCH = 10

COLLECTION = "kb_chunks"

# Index-based routing: query keywords -> topic bucket (strategy D).
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "agents": ["agent", "智能体", "multi-agent", "多智能体", "react", "推理", "工具调用", "tool use", "planner", "规划"],
    "engineering": ["工程", "工程化", "structured output", "结构化输出", "mcp", "pattern", "模式", "prompt", "提示词", "上下文工程", "context engineering"],
    "evals": ["评测", "评估", "eval", "benchmark", "judge", "裁判", "校准", "校验", "指标", "metric", "质量"],
    "memory": ["记忆", "memory", "长期记忆", "记忆检索", "reflection", "反思", "生成式代理", "上下文管理", "对话历史"],
    "retrieval": ["检索", "rag", "召回", "embedding", "向量", "bm25", "混合检索", "rerank", "重排", "chunk", "分块"],
}


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


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Minimal frontmatter parser (--- delimited key: value pairs)."""
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


def _split_long_text(text: str) -> list[str]:
    if len(text) <= CHUNK_SIZE:
        return [text] if text.strip() else []
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            # Prefer breaking on sentence/punctuation boundaries near the edge.
            window = text[start:end]
            cut = max(window.rfind("。"), window.rfind(". "), window.rfind("\n\n"))
            if cut > CHUNK_SIZE // 2:
                end = start + cut + 1
        pieces.append(text[start:end])
        start = end - CHUNK_OVERLAP if end < len(text) else end
    return [p for p in pieces if p.strip()]


def chunk_markdown(path: Path) -> list[Chunk]:
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    doc_id = path.stem
    title = meta.get("title") or doc_id
    topic = meta.get("topic") or "general"
    source_url = meta.get("source_url") or ""
    # Strip markdown noise that hurts both BM25 and embeddings.
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\[(\d+)\]", "", body)  # citation markers
    chunks: list[Chunk] = []
    sections = re.split(r"\n(?=#{2,3}\s)", body)
    if not sections:
        sections = [body]
    for sec in sections:
        sec_lines = sec.strip().splitlines()
        section_title = sec_lines[0].lstrip("#").strip() if sec_lines and sec_lines[0].startswith("#") else "intro"
        sec_text = "\n".join(sec_lines[1:] if sec_lines and sec_lines[0].startswith("#") else sec_lines).strip()
        for idx, piece in enumerate(_split_long_text(sec_text)):
            piece = piece.strip()
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
                )
            )
    return chunks


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
    cache.write_text("\n".join(json.dumps(asdict(c), ensure_ascii=False) for c in chunks), encoding="utf-8")
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
        # Field boosting: repeat the title so heading tokens outweigh body noise.
        self.corpus_tokens = [tokenize(f"{c.title} {c.title} {c.section} {c.text}") for c in chunks]
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def search(self, query: str, top_k: int = 10, min_rel: float = 0.0) -> list[tuple[Chunk, float]]:
        """min_rel drops weak tail results (score < min_rel * best score)."""
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self.doc_ids, scores), key=lambda x: x[1], reverse=True)[:top_k]
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
            pickle.dump({"doc_ids": self.doc_ids, "corpus_tokens": self.corpus_tokens}, f)


def load_bm25_index(chunks: list[Chunk] | None = None, force_rebuild: bool = False) -> BM25Index:
    chunks = chunks or load_all_chunks(force_rebuild=force_rebuild)
    return BM25Index(chunks)


class BailianEmbedder:
    def __init__(self, api_key: str | None = None, client: httpx.Client | None = None) -> None:
        self.api_key = api_key or os.environ.get("CONTENT_GENERATOR_BAILIAN_API_KEY", "")
        if not self.api_key:
            raise ValueError("Bailian API key is required for local KB embeddings.")
        self.client = client or httpx.Client(timeout=60.0)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), EMBED_BATCH):
            batch = [t[:6000] for t in texts[start : start + EMBED_BATCH]]
            response = self.client.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": EMBED_MODEL, "input": batch, "dimensions": EMBED_DIM},
            )
            if response.status_code != 200:
                bad = batch[0][:80]
                raise RuntimeError(f"Embedding batch {start} failed: HTTP {response.status_code}: {response.text[:200]} | first item: {bad!r}")
            data = sorted(response.json()["data"], key=lambda item: item["index"])
            vectors.extend([item["embedding"] for item in data])
        return vectors


def get_qdrant() -> "object":
    from qdrant_client import QdrantClient

    return QdrantClient(path=str(QDRANT_DIR))


def ensure_vector_index(chunks: list[Chunk], embedder: BailianEmbedder, force_rebuild: bool = False) -> None:
    from qdrant_client.models import Distance, PointStruct, VectorParams

    client = get_qdrant()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION in existing and not force_rebuild:
        return
    if COLLECTION in existing:
        client.delete_collection(COLLECTION)
    client.create_collection(COLLECTION, vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE))
    # Contextualized embedding (Anthropic contextual retrieval, simplified):
    # prefix each chunk with its document title + section so heading semantics
    # reach the vector ("Building Effective Agents" stays findable from a
    # chunk buried deep in the body).
    vectors = embedder.embed([f"{c.title} | {c.section} | {c.text}" for c in chunks])
    points = [
        PointStruct(id=idx, vector=vec, payload={"chunk_id": c.chunk_id, "doc_id": c.doc_id, "title": c.title, "topic": c.topic})
        for idx, (c, vec) in enumerate(zip(chunks, vectors))
    ]
    for start in range(0, len(points), 100):
        client.upsert(COLLECTION, points[start : start + 100])


def search_vector(query: str, chunks: list[Chunk], embedder: BailianEmbedder, top_k: int = 10) -> list[tuple[Chunk, float]]:
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = get_qdrant()
    vec = embedder.embed([query])[0]
    hits = client.query_points(COLLECTION, query=vec, limit=top_k).points
    chunk_by_id = {c.chunk_id: c for c in chunks}
    results = []
    for hit in hits:
        chunk = chunk_by_id.get(hit.payload.get("chunk_id"))
        if chunk:
            results.append((chunk, float(hit.score)))
    return results


def rrf_fuse(rankings: list[list[str]], k: int = 60, weights: list[float] | None = None) -> dict[str, float]:
    """Weighted reciprocal rank fusion.

    Equal weights reward every channel's rank equally; when one channel is
    noisy (e.g. cross-language BM25) its wrong top results can tie with the
    other channel's correct top-1. Weights let a trusted channel dominate.
    """
    weights = weights or [1.0] * len(rankings)
    scores: dict[str, float] = {}
    for ranking, weight in zip(rankings, weights):
        for pos, cid in enumerate(ranking):
            scores[cid] = scores.get(cid, 0.0) + weight / (k + pos + 1)
    return scores


def classify_query(query: str) -> str:
    """Classify a query as term-heavy or semantic (natural-language).

    Term-heavy queries name concrete artifacts (MemGPT, MT-Bench, DPR) where
    exact lexical match is reliable; semantic queries paraphrase intent where
    lexical signals break down (v4 finding: BM25 30%->44.7% on term queries).
    """
    tokens = tokenize(query)
    if not tokens:
        return "semantic"
    english = sum(1 for t in tokens if re.fullmatch(r"[a-z0-9+#._\-]{2,}", t))
    return "term" if english / len(tokens) >= 0.35 else "semantic"


def route_topic(query: str) -> str | None:
    lowered = query.lower()
    best_topic, best_hits = None, 0
    for topic, keywords in TOPIC_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in lowered)
        if hits > best_hits:
            best_topic, best_hits = topic, hits
    return best_topic if best_hits > 0 else None


def search(
    method: str,
    query: str,
    chunks: list[Chunk],
    bm25: BM25Index,
    embedder: BailianEmbedder,
    top_k: int = 10,
) -> list[tuple[Chunk, float]]:
    """Unified entry for the four retrieval strategies."""
    if method == "keyword":
        return bm25.search(query, top_k=top_k)
    if method == "vector":
        return search_vector(query, chunks, embedder, top_k=top_k)
    if method == "hybrid":
        # Relative-score filter keeps BM25's strong hits and drops the weak
        # tail that would otherwise occupy RRF's top ranks (v1 lesson: the
        # unfiltered Chinese-token tail drowned the vector channel).
        kw = bm25.search(query, top_k=20, min_rel=0.35)
        vec = search_vector(query, chunks, embedder, top_k=20)
        fused = rrf_fuse([[c.chunk_id for c, _ in kw], [c.chunk_id for c, _ in vec]])
        chunk_by_id = {c.chunk_id: c for c in chunks}
        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(chunk_by_id[cid], score) for cid, score in ranked if cid in chunk_by_id]
    if method == "router":
        # Query-aware weighted RRF (v5). Earlier iterations routed by topic
        # with hard filtering, which misfired on coarse/overlapping topic
        # labels (q26/q27/q28); classification by query type proved sturdier.
        qtype = classify_query(query)
        weights = [1.5, 1.0] if qtype == "term" else [0.5, 1.0]  # [bm25, vec]
        kw = bm25.search(query, top_k=20, min_rel=0.35)
        vec = search_vector(query, chunks, embedder, top_k=20)
        fused = rrf_fuse(
            [[c.chunk_id for c, _ in kw], [c.chunk_id for c, _ in vec]],
            weights=weights,
        )
        chunk_by_id = {c.chunk_id: c for c in chunks}
        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(chunk_by_id[cid], score) for cid, score in ranked if cid in chunk_by_id]
    raise ValueError(f"Unknown retrieval method: {method}")
