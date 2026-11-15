"""Unit 3.2 closing analysis: span asset stats + chunking baselines.

Reads knowledge/eval/local/span_annotations.json (annotate_spans.py output)
and reports:
1. GT hygiene: dirty (query, gt_chunk) pairs, verbatim resolution failures
2. Span shape: length distribution, span/chunk coverage ratio (how much of a
   chunk is actually the answer -- the headroom signal for chunk-level metrics)
3. Current-chunking baselines:
   - trivial: spans complete in current 800/120 chunking (they are annotated
     inside it, so ~100% -- sanity check)
   - informative: same 800-char window with ZERO overlap -- how many spans
     would be split? (= the truncation protection overlap=120 is buying)
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from knowledge.engine import kb_engine as kb  # noqa: E402

SPAN_PATH = REPO_ROOT / "knowledge" / "eval" / "local" / "span_annotations.json"


def clean_body(doc_id: str) -> str | None:
    raw = kb.KB_RAW_DIR / f"{doc_id}.md"
    if not raw.exists():
        return None
    _meta, body = kb.parse_frontmatter(raw.read_text(encoding="utf-8"))
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\[(\d+)\]", "", body)
    return body


def zero_overlap_complete(body: str, span_start: int, span_end: int, size: int = kb.CHUNK_SIZE) -> bool:
    """Would a same-size sliding window with ZERO overlap keep the span whole?"""
    if span_end - span_start > size:
        return False
    pos = 0
    while pos < len(body):
        end = min(pos + size, len(body))
        if end < len(body):
            window = body[pos:end]
            cut = max(window.rfind("。"), window.rfind(". "), window.rfind("\n\n"))
            if cut > size // 2:
                end = pos + cut + 1
        if pos <= span_start and span_end <= end:
            return True
        if end >= len(body):
            break
        pos = end  # zero overlap
    return False


def main() -> None:
    data = json.loads(SPAN_PATH.read_text(encoding="utf-8"))
    items = data["items"]
    print(f"asset: {len(items)} queries | calibration: {data['meta']['corpus']}")

    # 1. GT hygiene
    dirty = [qid for qid, a in items.items() if not a["clean"]]
    partial_dirty = [qid for qid, a in items.items() if not all(a["answer_here_flags"]) and a["clean"]]
    print(f"\n=== GT hygiene ===")
    print(f"clean: {len(items) - len(dirty)}/{len(items)} | dirty: {len(dirty)}")
    if dirty:
        print(f"  dirty ids: {dirty[:12]}")
    print(f"  (partial-dirty: some gt chunk lacks answer but another covers it: {len(partial_dirty)})")

    # 2. Span shape
    all_spans = [s for a in items.values() for s in a["spans"]]
    lens = [s["doc_end"] - s["doc_start"] for s in all_spans]
    lens.sort()
    n = len(lens)
    chunks_by_id = {c.chunk_id: c for c in kb.load_all_chunks()}
    ratios = []
    for s in all_spans:
        ch = chunks_by_id.get(s["chunk_id"])
        if ch:
            ratios.append((s["doc_end"] - s["doc_start"]) / max(ch.char_count, 1))
    ratios.sort()
    m = len(ratios)
    print(f"\n=== span shape ({n} spans) ===")
    print(f"span chars: p25={lens[n//4]} median={lens[n//2]} p75={lens[3*n//4]} max={lens[-1]}")
    print(f"span/chunk ratio: p25={ratios[m//4]:.2%} median={ratios[m//2]:.2%} p75={ratios[3*m//4]:.2%}")
    print(f"  -> answer occupies less than half its chunk for {sum(1 for r in ratios if r < 0.5)/m:.1%} of spans")

    # 3. Chunking baselines
    body_cache: dict[str, str] = {}
    trivial_ok = zero_ok = total = 0
    for a in items.values():
        for s in a["spans"]:
            doc_id = s["chunk_id"].split("::")[0]
            if doc_id not in body_cache:
                body_cache[doc_id] = clean_body(doc_id) or ""
            body = body_cache[doc_id]
            if not body:
                continue
            total += 1
            if any(0 <= s["doc_start"] - c.doc_offset and s["doc_end"] - c.doc_offset <= len(c.text)
                   for c in [chunks_by_id[s["chunk_id"]]]):
                trivial_ok += 1
            if zero_overlap_complete(body, s["doc_start"], s["doc_end"]):
                zero_ok += 1
    print(f"\n=== chunking baselines (n={total} spans) ===")
    print(f"current 800/120: spans complete = {trivial_ok}/{total} (trivially ~100%, spans annotated in-chunk)")
    print(f"simulated 800/0 (no overlap): spans complete = {zero_ok}/{total} = {zero_ok/total:.1%}")
    print(f"  -> overlap=120 protects {total - zero_ok} spans ({(total - zero_ok)/total:.1%}) from being split")


if __name__ == "__main__":
    main()
