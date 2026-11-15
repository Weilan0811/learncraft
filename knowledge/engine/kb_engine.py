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

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_RAW_DIR = REPO_ROOT / "knowledge" / "raw"
KB_WIKI_DIR = REPO_ROOT / "knowledge" / "wiki"
KB_INDEX_DIR = REPO_ROOT / "storage" / "kb"
QDRANT_DIR = REPO_ROOT / "storage" / "qdrant_kb"

WIKI_COLLECTION = "kb_wiki"  # bailian-era wiki collection (kept for rollback)
WIKI_COLLECTION_BGE = "kb_wiki_bgem3"  # BGE-M3-era wiki collection

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
EMBED_MODEL = "text-embedding-v3"
EMBED_DIM = 1024  # both Bailian text-embedding-v3 and BAAI/bge-m3 are 1024-dim
EMBED_BATCH = 10

COLLECTION = "kb_chunks"  # bailian-era dense collection (kept for rollback)
COLLECTION_BGE = "kb_chunks_bgem3"  # BGE-M3-era dense collection

BGE_MODEL_ENV = "BGE_M3_PATH"


def resolve_bge_model_path() -> Path:
    """Locate the local BAAI/bge-m3 snapshot: env override, then the
    project-root convention (`.models/bge-m3`, gitignored). Worktrees look at
    the parent repo root, so one download serves every worktree."""
    env = os.environ.get(BGE_MODEL_ENV, "").strip()
    candidates = [Path(env)] if env else []
    candidates += [REPO_ROOT / ".models" / "bge-m3", REPO_ROOT.parent.parent / ".models" / "bge-m3"]
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


def _active_collection(wiki: bool = False) -> str:
    """Dense collection matching the active embedder. Dimensions are
    compatible (1024) but the vector spaces are NOT -- mixing embedders inside
    one collection is silent corruption, so each era gets its own collection."""
    bailian = _active_embedder_kind() == "bailian"
    if wiki:
        return WIKI_COLLECTION if bailian else WIKI_COLLECTION_BGE
    return COLLECTION if bailian else COLLECTION_BGE

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
    # platform | attachment (task-scoped user material) | wiki (distilled layer).
    # Legacy caches written before this field default to "platform" on load.
    scope: str = "platform"
    # Wiki pages only: their page's source_refs (doc_id#Section,... or doc_id,...),
    # used to expand a wiki hit into raw evidence chunks (schema 4.4). Empty for raw chunks.
    source_refs: str = ""
    # Start offset of this chunk inside the doc's CLEANED body (the post-regex
    # text in _chunk_body, before per-piece stripping). Enables
    # chunking-independent answer-span coordinates: a span (doc_id, start, end)
    # can be re-evaluated against any future chunking strategy without
    # re-annotation. 0 for legacy caches -- force_rebuild to populate.
    doc_offset: int = 0


# ---- structural junk filter (2026-11-14, user-audit driven) -----------------
# 3.5 manual review found corpus junk entering retrieval AND the eval sampler:
# References/Citation sections, LaTeX/SVG debris (self-rag), nav-link lists.
# Decided: filter at INDEX-BUILD time (chunks.jsonl & chunk_id space untouched,
# so all v8 eval assets stay valid); ALSO used by the 3.4 sampler and ingest.
# "Junk not retrievable" is operationally equivalent to "junk absent", without
# invalidating downstream caches. Narrative-but-thin chunks are NOT junk --
# ranking (rerank) handles those, deletion risks context cuts.
_JUNK_SECTION_RE = re.compile(
    r"references|citations?|bibliography|参考文献|参考资料|引用文献|致谢|acknowledg(?:ement)?s?|"
    r"further reading|external links|see also",
    re.I,
)
_JUNK_LATEX_RE = re.compile(r"lxSVG@|pgfsys@|lx@inpgf", re.I)
_JUNK_NAV_HEADING = re.compile(r"^#{1,6}\s*(目录|contents|table of contents)\s*$", re.I)


def is_structural_junk(chunk: "Chunk") -> bool:
    """Deterministic, zero-LLM structural junk detection.

    Rules (dry-run v2 2026-11-14: 417/3255 = 12.8% of corpus):
    1. section heading is a References/Citation/Acknowledgement-type node
    2. text contains LaTeX/SVG internal command debris (PDF-extraction artifacts)
    3. nav block: mostly SHORT markdown link lines (TOC / sidebar dump).
       v1 (ratio-only) misfired on academic prose whose inline citations are
       markdown links (Related Work paragraphs, citation sentences) -- fixed by
       requiring mean link-line length < 120 chars: real TOC/sidebar lines are
       short, citation-bearing narrative lines run 200-800 chars.
    """
    if _JUNK_SECTION_RE.search(chunk.section or ""):
        return True
    if _JUNK_LATEX_RE.search(chunk.text):
        return True
    lines = [ln for ln in chunk.text.splitlines() if ln.strip()]
    if lines:
        link = [ln for ln in lines if re.search(r"\[[^\]]*\]\(", ln) or re.match(r"^- \[[ x]\]", ln)]
        if link and len(link) / len(lines) > 0.6 and sum(len(ln) for ln in link) / len(link) < 120:
            return True
    if _JUNK_NAV_HEADING.match(chunk.text.strip().splitlines()[0] if chunk.text.strip() else ""):
        return True
    return False


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


def _split_long_text_spans(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> "list[tuple[str, int]]":
    """Sliding-window split keeping each piece's exact start offset.

    Same cutting algorithm as the historical _split_long_text (piece content
    identical after stripping); returns (piece, offset) where offset points at
    the piece AFTER leading-whitespace removal, so (offset, len(piece)) are
    exact coordinates inside `text`. Parameters are overridable for chunking
    experiments (unit 3.3); defaults keep historical behavior byte-identical.
    """
    if chunk_overlap >= chunk_size:
        raise ValueError(f"chunk_overlap ({chunk_overlap}) must be smaller than chunk_size ({chunk_size})")
    if len(text) <= chunk_size:
        stripped = text.strip()
        return [(stripped, 0)] if stripped else []
    pieces: list[tuple[str, int]] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # Prefer breaking on sentence/punctuation boundaries near the edge.
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
    """Shared chunking pipeline for both file-sourced and text-sourced documents.

    Section and window boundaries are tracked as offsets into the CLEANED body
    (post regex passes) so every chunk carries doc_offset -- the anchor for
    chunking-independent answer-span annotations (unit 3.2).
    """
    # Strip markdown noise that hurts both BM25 and embeddings.
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\[(\d+)\]", "", body)  # citation markers
    chunks: list[Chunk] = []
    # Exact section boundaries: the split regex keeps only the position of the
    # separating "\n"; finditer reproduces re.split's boundaries with offsets.
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
            # heading line occupies its content plus the newline it ends with
            heading_len = len(sec_lines[0]) + 1
        else:
            section_title = "intro"
            joined = "\n".join(sec_lines)
            heading_len = 0
        sec_text = joined.strip()
        if not sec_text:
            continue
        # Offset of sec_text inside the cleaned body: section start + stripped
        # leading whitespace of the section + heading line (content + \n) +
        # stripped leading whitespace of the content under the heading.
        content_base = sec_start + sec_lead + heading_len + (len(joined) - len(joined.lstrip()))
        # enumerate BEFORE the length filter, exactly like the historical code:
        # skipped short pieces still consume an idx, keeping chunk_id stable
        # against every cache/eval reference ever written.
        for idx, (piece, piece_off) in enumerate(_split_long_text_spans(sec_text, chunk_size, chunk_overlap)):
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


def para_chunk_body(
    doc_id: str,
    title: str,
    topic: str,
    source_url: str,
    scope: str,
    body: str,
    target: int = 600,
    max_len: int = 900,
) -> list[Chunk]:
    """Paragraph-aggregation chunking (unit 3.3 candidate).

    Splits each section on blank lines, then greedily merges adjacent paragraph
    ranges until ~target chars. The merged chunk text is an EXACT substring of
    the cleaned body (original newlines preserved), so doc_offset + char_count
    are precise coordinates like the window chunker's. Overlong paragraphs
    (>max_len) fall back to the window splitter with zero overlap.
    """
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
        content_base = sec_start + sec_lead + heading_len + (len(joined) - len(joined.lstrip()))

        # Paragraph ranges [start, end) inside sec_text, split on blank lines.
        ranges: list[tuple[int, int]] = []
        cursor = 0
        for m in re.finditer(r"[^\n](?:\n(?!\n)[^\n])*", sec_text):
            start, end = m.start(), m.end()
            if not sec_text[start:end].strip():
                continue
            # merge trailing/leading whitespace into the range edges
            while end < len(sec_text) and sec_text[end] in "\n":
                end += 1
            while start > 0 and sec_text[start - 1] in "\n":
                start -= 1
            ranges.append((start, end))
            cursor = end
        if not ranges:
            continue

        # Greedy merge: grow the buffer until adding the next paragraph would
        # exceed target, then flush. Buffer ranges are contiguous by
        # construction (adjacent paragraph ranges with their separators).
        merged: list[tuple[int, int]] = []
        buf_start, buf_end = ranges[0]
        for s, e in ranges[1:]:
            if (e - buf_start) > target and (buf_end - buf_start) >= 60:
                merged.append((buf_start, buf_end))
                buf_start, buf_end = s, e
            else:
                buf_end = e
        merged.append((buf_start, buf_end))

        idx = 0
        for s, e in merged:
            seg = sec_text[s:e]
            stripped_seg = seg.strip()
            if not stripped_seg:
                continue
            pieces: list[tuple[str, int]] = []
            if len(stripped_seg) > max_len:
                # rare: one giant paragraph -- window-split with no overlap,
                # offsets translated back into sec_text coordinates
                lead = len(seg) - len(seg.lstrip())
                for piece, off in _split_long_text_spans(stripped_seg, chunk_size=max_len, chunk_overlap=0):
                    if len(piece) >= 60:
                        pieces.append((piece, s + lead + off))
            else:
                pieces.append((stripped_seg, s + (len(seg) - len(seg.lstrip()))))
            for piece, off in pieces:
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc_id}::{section_title}::p{idx}",
                        doc_id=doc_id,
                        title=title,
                        topic=topic,
                        section=section_title,
                        text=piece,
                        source_url=source_url,
                        char_count=len(piece),
                        scope=scope,
                        doc_offset=content_base + off,
                    )
                )
                idx += 1
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
    """Chunk raw text (user-uploaded material) with the same pipeline as files."""
    return _chunk_body(doc_id=doc_id, title=title, topic=topic, source_url=source_url, scope=scope, body=text)


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


def chunk_wiki_markdown(path: Path) -> list[Chunk]:
    """Chunk a compiled wiki page. doc_id = wiki/<sub>/<stem> (matches its wikilink path)."""
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    doc_id = f"wiki/{path.parent.name}/{path.stem}"
    return _chunk_body(
        doc_id=doc_id,
        title=meta.get("title") or path.stem,
        topic=(meta.get("tags") or "general").split(",")[0].strip(),
        source_url=meta.get("source_doc") or "",
        scope="wiki",
        body=body,
    )


def load_wiki_chunks(force_rebuild: bool = False) -> list[Chunk]:
    """Wiki-layer chunks (scope=wiki), cached separately from raw so the raw
    index and every existing consumer stay untouched (three-arm baseline)."""
    cache = KB_INDEX_DIR / "chunks-wiki.jsonl"
    if cache.exists() and not force_rebuild:
        chunks = []
        for line in cache.read_text(encoding="utf-8").splitlines():
            if line.strip():
                chunks.append(Chunk(**json.loads(line)))
        if chunks:
            return chunks
    chunks: list[Chunk] = []
    for sub in ("summaries", "concepts", "comparisons"):
        for md in sorted((KB_WIKI_DIR / sub).glob("*.md")):
            meta, _ = parse_frontmatter(md.read_text(encoding="utf-8"))
            page_chunks = chunk_wiki_markdown(md)
            refs = meta.get("source_refs", "")
            for c in page_chunks:
                c.source_refs = refs
            chunks.extend(page_chunks)
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
        self.bm25 = BM25Okapi(self.corpus_tokens) if self.corpus_tokens else None

    def search(self, query: str, top_k: int = 10, min_rel: float = 0.0) -> list[tuple[Chunk, float]]:
        """min_rel drops weak tail results (score < min_rel * best score)."""
        if self.bm25 is None:
            return []
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
    chunks = chunks if chunks is not None else load_all_chunks(force_rebuild=force_rebuild)
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


class Embedder:
    """Structural interface: any object with ``embed(texts) -> vectors``.
    Bailian (cloud) and BGE-M3 (local) are interchangeable behind this."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class BGEM3Embedder:
    """Local dense embeddings via BAAI/bge-m3 (1024-dim, 8K ctx).

    Lazy-loads the 2.3GB checkpoint on first embed() so importing kb_engine
    stays cheap. fp16 on CUDA automatically. BGE-M3 also supports
    sparse/colbert outputs -- unused here, the dense arm is the swap target.
    """

    def __init__(self, model_path: str | Path | None = None, batch_size: int = 8, max_length: int = 2048) -> None:
        self.model_path = str(model_path) if model_path else str(resolve_bge_model_path())
        self.batch_size = batch_size
        self.max_length = max_length  # chunks are ~800 chars; 2048 covers the longest contextualized input with headroom
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


def get_embedder(kind: str | None = None) -> Embedder:
    """Embedder factory. Default follows KB_EMBEDDER env (bge_m3 since unit 3.1;
    set KB_EMBEDDER=bailian to roll back to the cloud embedder + kb_chunks collection)."""
    kind = (kind or _active_embedder_kind()).lower()
    if kind == "bge_m3":
        return BGEM3Embedder()
    if kind == "bailian":
        return BailianEmbedder()
    raise ValueError(f"unknown embedder kind: {kind!r} (expected 'bge_m3' or 'bailian')")


_QDRANT_CLIENT: "object | None" = None


def get_qdrant() -> "object":
    """Process-level singleton. Local-mode QdrantClient reopens/mmaps the whole
    storage on every construction -- per-request construction (the old behavior)
    made each vector query pay seconds of I/O, in eval AND in the FastAPI app."""
    global _QDRANT_CLIENT
    if _QDRANT_CLIENT is None:
        from qdrant_client import QdrantClient

        _QDRANT_CLIENT = QdrantClient(path=str(QDRANT_DIR))
    return _QDRANT_CLIENT


def close_qdrant() -> None:
    """Explicitly close the local-mode client and drop the singleton.

    WHY THIS EXISTS (2026-11-14, found by the unit-4 ingest experiment): local
    QdrantClient persists lazily and flushes in close(). Relying on __del__ at
    interpreter shutdown FAILS silently (close() raises ImportError while
    sys.meta_path is already None) -- schema-level ops (delete_collection /
    create_collection) were lost, while point upserts happened to be
    write-through, so build_kb --rebuild "succeeded" but the on-disk collection
    silently stayed stale. Any process that mutates collections MUST call this
    before exit; read-only processes call it too for hygiene."""
    global _QDRANT_CLIENT
    if _QDRANT_CLIENT is not None:
        try:
            _QDRANT_CLIENT.close()
        except Exception:  # noqa: BLE001 -- shutting down; nothing to recover
            pass
        _QDRANT_CLIENT = None


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
    client.create_collection(collection, vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE))
    # Contextualized embedding (Anthropic contextual retrieval, simplified):
    # prefix each chunk with its document title + section so heading semantics
    # reach the vector ("Building Effective Agents" stays findable from a
    # chunk buried deep in the body).
    vectors = embedder.embed([f"{c.title} | {c.section} | {c.text}" for c in chunks])
    points = [
        PointStruct(id=idx, vector=vec, payload={"chunk_id": c.chunk_id, "doc_id": c.doc_id, "title": c.title, "topic": c.topic, "scope": c.scope})
        for idx, (c, vec) in enumerate(zip(chunks, vectors))
    ]
    for start in range(0, len(points), 100):
        client.upsert(collection, points[start : start + 100])
    # Post-upsert verification: local-mode persistence has shown silent-failure
    # modes (2026-11-14) -- never trust a rebuild without counting.
    final = client.count(collection, exact=True).count
    if final != len(points):
        raise RuntimeError(
            f"vector index verification failed: collection {collection!r} has {final} points, expected {len(points)}. "
            "Run build_kb.py --rebuild (it wipes the storage dir first)."
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
    """In-memory dense retrieval for small dynamic chunk sets (task attachments).

    A tiny namespace (a handful of user-uploaded docs) doesn't justify a
    shared-index write; the chunk vectors are computed on the fly and can be
    cached per document content hash to avoid re-embedding on every retrieval.
    Uses the same contextualized embedding input as ensure_vector_index.
    """
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
    ranked = sorted(zip(range(len(chunks)), sims), key=lambda x: x[1], reverse=True)[:top_k]
    return [(chunks[i], float(s)) for i, s in ranked if s > 0.01]


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
    embedder: Embedder,
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


# ---------------------------------------------------------------------------
# Parent-child retrieval: wiki hit -> deterministic raw-evidence expansion.
# ---------------------------------------------------------------------------

def _norm_section(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _merge_broken_refs(source_refs: str, known_docs: set[str]) -> list[str]:
    """Re-merge refs that a comma inside a heading split into fake refs.

    Flat frontmatter stores source_refs comma-separated (schema 4.1), but a
    raw heading may itself contain commas ('Building blocks, workflows, and
    agents'). Splitting naively yields fake docs like 'workflows'. Since doc
    ids are known (raw stems), a fragment whose doc part is unknown is glued
    back onto the previous ref.
    """
    merged: list[str] = []
    for token in [t.strip() for t in source_refs.split(",") if t.strip()]:
        doc_part = token.partition("#")[0].strip()
        if merged and doc_part not in known_docs:
            merged[-1] = f"{merged[-1]},{token}"
        else:
            merged.append(token)
    return merged


def expand_to_raw(
    source_refs: str,
    raw_chunks: list[Chunk],
    strategy: str = "round_robin",
) -> tuple[list[Chunk], dict[str, int]]:
    """Deterministically expand a wiki page's source_refs into raw evidence chunks.

    Section-level refs (doc_id#Section) -> chunks of that section (normalized
    match). Unresolvable sections degrade to doc-level expansion (recall over
    precision -- a broken section anchor still points at the right document);
    only unknown docs count as hard failures. Doc-level refs -> all chunks.

    Returns (deduped chunks, stats) where stats splits refs into
    exact / degraded / failed.

    strategy="round_robin" (default): refs rotate in the output so a doc-level
    anchor's 200 chunks cannot crowd other refs out of any top-k window.
    strategy="raw": refs concatenated in ref order -- the full evidence pool,
    for callers that rank the pool themselves (pool_rerank).
    """
    raw_by_doc: dict[str, list[Chunk]] = {}
    for c in raw_chunks:
        raw_by_doc.setdefault(c.doc_id, []).append(c)
    known_docs = set(raw_by_doc)

    seen: set[str] = set()
    stats = {"refs_total": 0, "refs_exact": 0, "refs_degraded": 0, "refs_failed": 0}
    picks_per_ref: list[list[Chunk]] = []
    for ref in _merge_broken_refs(source_refs, known_docs):
        stats["refs_total"] += 1
        doc, _, section = ref.partition("#")
        candidates = raw_by_doc.get(doc, [])
        if not candidates:
            stats["refs_failed"] += 1
            continue
        if not section:
            picked = candidates  # doc-level anchor (concept/comparison pages)
            stats["refs_exact"] += 1
        else:
            picked = [c for c in candidates if c.section == section]
            if not picked:
                picked = [c for c in candidates if _norm_section(c.section) == _norm_section(section)]
            if picked:
                stats["refs_exact"] += 1
            else:
                picked = candidates  # degrade: section unknown, doc is still right
                stats["refs_degraded"] += 1
        fresh = [c for c in picked if c.chunk_id not in seen]
        seen.update(c.chunk_id for c in fresh)
        if fresh:
            picks_per_ref.append(fresh)

    if strategy == "raw":
        return [c for p in picks_per_ref for c in p], stats

    expanded: list[Chunk] = []
    idx = 0
    while any(idx < len(p) for p in picks_per_ref):
        for p in picks_per_ref:
            if idx < len(p):
                expanded.append(p[idx])
        idx += 1
    return expanded, stats


def _fetch_pool_vectors(chunk_ids: list[str], collection: str) -> dict[str, list[float]]:
    """Pull stored vectors for the given chunk ids from Qdrant (local, zero API cost)."""
    from qdrant_client.models import FieldCondition, Filter, MatchAny

    client = get_qdrant()
    by_id: dict[str, list[float]] = {}
    step = 400  # scroll window; MatchAny has a large but finite limit
    for start in range(0, len(chunk_ids), step):
        window = chunk_ids[start : start + step]
        points, _offset = client.scroll(
            collection,
            scroll_filter=Filter(must=[FieldCondition(key="chunk_id", match=MatchAny(any=window))]),
            with_payload=True,
            with_vectors=True,
            limit=step + 10,
        )
        for p in points:
            if p.vector is not None:
                by_id[p.payload.get("chunk_id")] = list(p.vector)
    return by_id


def _pool_rerank_ranking(
    pool: list[Chunk],
    query_vector: list[float],
) -> list[tuple[Chunk, float]]:
    """Rank the expansion pool by local cosine against the query vector.

    The wiki layer only decided WHICH pages are relevant; ranking chunks inside
    the pool by vector similarity restores per-chunk resolution that page-rank
    inheritance lacks. Vectors come from the raw collection (already stored at
    build time), so this costs zero API calls. Chunks without a stored vector
    keep their pool position at the tail.
    """
    import math

    by_chunk = {c.chunk_id: c for c in pool}
    stored = _fetch_pool_vectors([c.chunk_id for c in pool], COLLECTION)

    def cosine(a: list[float], b: list[float]) -> float:
        num = sum(x * y for x, y in zip(a, b))
        da = math.sqrt(sum(x * x for x in a)) or 1e-9
        db = math.sqrt(sum(y * y for y in b)) or 1e-9
        return num / (da * db)

    ranked: list[tuple[Chunk, float]] = []
    tail: list[Chunk] = []
    for c in pool:
        vec = stored.get(c.chunk_id)
        if vec:
            ranked.append((c, cosine(query_vector, vec)))
        else:
            tail.append(c)
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked + [(c, 0.0) for c in tail]


def search_wiki(
    query: str,
    wiki_chunks: list[Chunk],
    wiki_bm25: BM25Index,
    embedder: Embedder,
    raw_chunks: list[Chunk],
    top_k: int = 10,
    expand_strategy: str = "round_robin",
) -> tuple[list[tuple[Chunk, float]], dict[str, int]]:
    """Arm B: hybrid retrieval over the wiki layer, expanded to raw evidence.

    Returns (raw chunks ranked, fidelity stats).

    expand_strategy="round_robin" (default): evidence slots rotate across hit
    pages (and refs inside a page) -- every wiki hit gets equal representation
    in the top-k window. Ranking resolution within a page: none (page-rank
    inherited).

    expand_strategy="pool_rerank": all hit pages expand into one full evidence
    pool (refs concatenated), then the pool is ranked by local cosine against
    the query vector (vectors fetched from the raw collection, zero API cost).
    "Wiki decides the pages, vector similarity decides the chunks."
    """
    kw = wiki_bm25.search(query, top_k=20, min_rel=0.35)
    query_vec = embedder.embed([query])[0]
    vec = search_vector(query, wiki_chunks, embedder, top_k=20, collection=_active_collection(wiki=True), query_vector=query_vec)
    fused = rrf_fuse([[c.chunk_id for c, _ in kw], [c.chunk_id for c, _ in vec]])
    wiki_by_id = {c.chunk_id: c for c in wiki_chunks}
    ranked_pages: list[str] = []
    for cid, _score in sorted(fused.items(), key=lambda x: x[1], reverse=True):
        chunk = wiki_by_id.get(cid)
        if chunk and chunk.doc_id not in ranked_pages:
            ranked_pages.append(chunk.doc_id)
        if len(ranked_pages) >= top_k:
            break

    raw_by_id = {c.chunk_id: c for c in raw_chunks}
    fidelity = {"refs_total": 0, "refs_exact": 0, "refs_degraded": 0, "refs_failed": 0}

    if expand_strategy == "pool_rerank":
        # Full evidence pool across all hit pages, then local vector rerank.
        pool: list[Chunk] = []
        pool_seen: set[str] = set()
        for page_doc in ranked_pages:
            page_chunk = next((c for c in wiki_chunks if c.doc_id == page_doc), None)
            if page_chunk is None:
                continue
            evidence, stats = expand_to_raw(page_chunk.source_refs, raw_chunks, strategy="raw")
            for k, v in stats.items():
                fidelity[k] = fidelity.get(k, 0) + v
            for c in evidence:
                if c.chunk_id not in pool_seen and c.chunk_id in raw_by_id:
                    pool_seen.add(c.chunk_id)
                    pool.append(raw_by_id[c.chunk_id])
        ranked_pool = _pool_rerank_ranking(pool, query_vec)
        return ranked_pool[:top_k], fidelity

    # round_robin: inherit page rank, rotate evidence across pages.
    picks_per_page: list[list[tuple[Chunk, float]]] = []
    for page_rank, page_doc in enumerate(ranked_pages):
        page_chunk = next((c for c in wiki_chunks if c.doc_id == page_doc), None)
        if page_chunk is None:
            continue
        evidence, stats = expand_to_raw(page_chunk.source_refs, raw_chunks)
        for k, v in stats.items():
            fidelity[k] = fidelity.get(k, 0) + v
        score = 1.0 / (page_rank + 1)
        picks_per_page.append([(raw_by_id[c.chunk_id], score) for c in evidence if c.chunk_id in raw_by_id])

    # Interleave across pages: one hit page's doc-level expansion can be 100+
    # chunks, and sequential concat would fill the whole top-k with page 1.
    # Two-level round-robin (across pages, refs already rotate inside a page)
    # gives every hit page evidence slots proportional to... nothing -- equal,
    # which is the point: the wiki hit itself is the first-class signal.
    expanded: list[tuple[Chunk, float]] = []
    idx = 0
    while any(idx < len(p) for p in picks_per_page):
        for p in picks_per_page:
            if idx < len(p):
                expanded.append(p[idx])
        idx += 1
    deduped: list[tuple[Chunk, float]] = []
    seen: set[str] = set()
    for c, s in expanded:
        if c.chunk_id not in seen:
            seen.add(c.chunk_id)
            deduped.append((c, s))
    return deduped[:top_k], fidelity


def search_fused(
    query: str,
    chunks: list[Chunk],
    bm25: BM25Index,
    embedder: Embedder,
    wiki_chunks: list[Chunk],
    wiki_bm25: BM25Index,
    top_k: int = 10,
    expand_strategy: str = "round_robin",
    pool_construction: str = "rrf",
) -> list[tuple[Chunk, float]]:
    """Arm C: raw direct retrieval + wiki expansion, combined into one ranking.

    pool_construction selects how the two channels merge (unit 2.5 experiment):
    - "rrf":        rank-based RRF over raw top-k and wiki-expanded top-k
                    (v6 behaviour, equal weights).
    - "union_top":  raw top-k ∪ wiki-expanded top-k deduped, truncated at k in
                    RRF order (user option 1).
    - "big_pool":   raw top-50 + wiki-expanded pool -> one ranking cut at k
                    (user option 2; large-pool funnel).
    - "quota":      k/2 raw top slots + k/2 wiki top slots interleaved
                    (user option 3; fixed quota per channel).
    """
    raw_ranked = search("router", query, chunks, bm25, embedder, top_k=top_k if pool_construction != "big_pool" else 50)
    wiki_ranked, _fidelity = search_wiki(
        query, wiki_chunks, wiki_bm25, embedder,
        raw_chunks=chunks, top_k=top_k, expand_strategy=expand_strategy,
    )
    raw_ids = [c.chunk_id for c, _ in raw_ranked]
    wiki_ids = [c.chunk_id for c, _ in wiki_ranked]
    chunk_by_id = {c.chunk_id: c for c in chunks}

    if pool_construction == "quota":
        half = top_k // 2
        merged: list[tuple[Chunk, float]] = []
        seen: set[str] = set()
        idx = 0
        while len(merged) < top_k and (idx < half or idx < len(raw_ids)):
            for lst, score in ((raw_ids, 1.0), (wiki_ids, 1.0)):
                if idx < half and idx < len(lst) and lst[idx] not in seen:
                    seen.add(lst[idx])
                    merged.append((chunk_by_id[lst[idx]], score))
            idx += 1
        # fill remaining slots from the other channel's tail
        for lst in (raw_ids, wiki_ids):
            for cid in lst:
                if len(merged) >= top_k:
                    break
                if cid not in seen:
                    seen.add(cid)
                    merged.append((chunk_by_id[cid], 0.5))
        return merged[:top_k]

    if pool_construction == "union_top":
        union_ids = list(dict.fromkeys(raw_ids + wiki_ids))[:top_k]
        scores = rrf_fuse([raw_ids, wiki_ids], weights=[1.0, 1.0])
        return [(chunk_by_id[cid], scores.get(cid, 0.0)) for cid in union_ids if cid in chunk_by_id]

    if pool_construction == "big_pool":
        wiki_pool_ids = [c.chunk_id for c, _ in wiki_ranked]
        scores = rrf_fuse([raw_ids, wiki_pool_ids], weights=[1.0, 1.0])
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(chunk_by_id[cid], s) for cid, s in ranked if cid in chunk_by_id]

    fused = rrf_fuse([raw_ids, wiki_ids], weights=[1.0, 1.0])
    ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [(chunk_by_id[cid], score) for cid, score in ranked if cid in chunk_by_id]
