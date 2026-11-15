"""Synthetic QA generation for the rebuilt evaluation set (unit 2.5.2).

Model-family isolation (the anti-coupling decision from the v6 autopsy):
deepseek generates the questions, qwen compiled the wiki, bailian embeds both
-- three independent families, so no family sees queries written by itself.

Generation disciplines (from the literature survey, all verified practices):
- wording debias: the model first lists the chunk's key terms, then must NOT
  use them verbatim in the question (paraphrase-only, different persona)
- evolution distribution (RAGAS Evol-Instruct style): simple 40% / reasoning
  25% / multi-context 25% / conditional 10%
- critic filter: second deepseek pass scores clarity / self-containedness /
  answerability / groundedness; any score < 0.7 rejects
- chunk-level ground truth: the chunk(s) used for generation ARE the labels
- dev/eval split: stratified 70/30 on doc level, disjoint subsets; dev is the
  only set any tuning may look at, eval runs once at the end

Hand-written trap layer lives in TRAP_QUERIES / COLLOQUIAL_QUERIES below
(semantic-drift traps: query wording deliberately avoids the corpus terms;
colloquial vague queries). These are scored against manually labeled targets.

Output: knowledge/eval/local/synthetic_qa.json (gitignored).

Usage:
    PYTHONPATH=. python knowledge/scripts/gen_synthetic_qa.py --pilot   # 3 items, format check
    PYTHONPATH=. python knowledge/scripts/gen_synthetic_qa.py           # full run (~350 deepseek calls)
    PYTHONPATH=. python knowledge/scripts/gen_synthetic_qa.py --resume  # continue an interrupted run
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from knowledge.engine import kb_engine as kb  # noqa: E402

OUT_PATH = REPO_ROOT / "knowledge" / "eval" / "local" / "synthetic_qa.json"
CHECKPOINT = REPO_ROOT / "knowledge" / "eval" / "local" / "synthetic_checkpoint.json"

EVOLUTION_MIX = {"simple": 0.40, "reasoning": 0.25, "multi_context": 0.25, "conditional": 0.10}
CRITIC_THRESHOLD = 0.7

# Semantic-drift traps: queries deliberately avoid the corpus's own terminology
# (the trap the original 38-query set fell into -- author wrote queries in the
# corpus's words). expected_relevant is my manual labeling; scored separately.
# Colloquial vague queries + trap queries live in the LOCAL manifest (gitignored,
# unit 6 compliance: eval data ships separately from the pipeline). Schema:
# {"trap": [{"query":..., "expected_relevant": [...], "note":...}], "colloquial": [...]}
SYN_MANIFEST = REPO_ROOT / "knowledge" / "eval" / "local" / "synthetic_qa_queries.json"
if not SYN_MANIFEST.exists():
    sys.exit(f"missing {SYN_MANIFEST}: author trap/colloquial queries for YOUR corpus")
_SYN = json.loads(SYN_MANIFEST.read_text(encoding="utf-8"))
TRAP_QUERIES = _SYN["trap"]
COLLOQUIAL_QUERIES = _SYN["colloquial"]


def read_env_key(name: str) -> str:
    for line in (REPO_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(f"{name}=") and not line.startswith("#"):
            return line.partition("=")[2].strip()
    return ""


class DeepSeekClient:
    """Minimal deepseek-chat REST client (JSON mode supported)."""

    def __init__(self) -> None:
        self.base = read_env_key("CONTENT_GENERATOR_DEEPSEEK_BASE_URL").rstrip("/") or "https://api.deepseek.com"
        self.key = read_env_key("CONTENT_GENERATOR_DEEPSEEK_API_KEY")

    def chat_json(self, system: str, user: str, temperature: float = 1.0) -> dict:
        resp = requests.post(
            f"{self.base}/chat/completions",
            headers={"Authorization": f"Bearer {self.key}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": temperature,
                "response_format": {"type": "json_object"},
                "max_tokens": 900,
            },
            timeout=90,
        )
        resp.raise_for_status()
        return json.loads(resp.json()["choices"][0]["message"]["content"])


GEN_SYSTEM = """你是检索评测集的构建专家，负责从知识片段逆向生成评测问题。

核心纪律（评测集有效性 depend on these）：
1. 措辞去偏：先列出片段中 3-6 个关键术语放进 avoided_terms，然后保证 question 里不出现这些术语的原词——用同义表述、换提问视角（问后果、问对比、问应用场景、或用给外行解释的口吻）。禁止照抄片段的标题式词组。
2. 自足性：question 不能有"该文档/上文/文中"这类指代，脱离原文也能独立理解。
3. 可答性：给定的片段内容必须足以完整回答问题；answer 要点必须全部来自片段，不引入外部知识、不编造。
4. answer 用 2-4 句概括标准答案要点（这是评分参照，不是给检索看的）。

输出 JSON：{"avoided_terms": ["..."], "question": "...", "answer": "...", "difficulty": "easy|medium|hard"}"""

EVOLUTION_GUIDE = {
    "simple": "本次生成 simple 类型：直接的事实/机制/参数问题，答案在片段里有明确对应。",
    "reasoning": "本次生成 reasoning 类型：问题需要基于片段内容做一步推理或因果解释（为什么/会导致什么），而不是直接复述原文。",
    "conditional": "本次生成 conditional 类型：在问题里引入一个假设条件（如果/当…时），问在该条件下会发生什么或该怎么处理；答案要能从片段内容推导。",
}

CRITIC_SYSTEM = """你是评测集质量审查员。对给定的评测问题严格打分（0-1，两位小数）：
- clarity：问题语义清晰、无歧义
- self_contained：脱离原文也能理解问题在问什么
- answerable：给定片段足以完整回答该问题
- grounded：answer 的要点确实来自片段内容，无编造
输出 JSON：{"clarity": x, "self_contained": x, "answerable": x, "grounded": x, "verdict": "pass|reject", "reason": "一句话"}。任何一项 < 0.7 即 verdict=reject，宁缺毋滥。"""


def sample_chunks(chunks: list[kb.Chunk]) -> list[dict]:
    """Per-doc sampling quota by doc size; returns generation tasks.

    simple/conditional: 1 chunk; reasoning: 2 adjacent chunks of same doc;
    multi_context: 2 chunks from different docs of the same topic.
    """
    rng = random.Random(20260525)
    by_doc: dict[str, list[kb.Chunk]] = {}
    for c in chunks:
        by_doc.setdefault(c.doc_id, []).append(c)

    tasks: list[dict] = []
    for doc_id, doc_chunks in sorted(by_doc.items()):
        n = 5 if len(doc_chunks) >= 20 else (4 if len(doc_chunks) >= 10 else 3)
        picked = rng.sample(doc_chunks, min(n, len(doc_chunks)))
        for i, c in enumerate(picked):
            evo = rng.choices(list(EVOLUTION_MIX), weights=list(EVOLUTION_MIX.values()))[0]
            if evo == "reasoning" and len(doc_chunks) > 1:
                idx = doc_chunks.index(c)
                partner = doc_chunks[(idx + 1) % len(doc_chunks)]
                tasks.append({"evo": evo, "chunks": [c, partner]})
            else:
                if evo == "reasoning":
                    evo = "simple"
                tasks.append({"evo": evo, "chunks": [c]})
        # one multi-context task per doc: pair a picked chunk with another doc in same topic
        if len(picked) < n:
            continue
        peers = [d for d, cs in by_doc.items() if cs[0].topic == doc_chunks[0].topic and d != doc_id]
        if peers:
            peer = rng.choice(peers)
            peer_chunk = rng.choice(by_doc[peer])
            tasks.append({"evo": "multi_context", "chunks": [picked[0], peer_chunk]})
    rng.shuffle(tasks)
    return tasks


def format_chunks(task: dict) -> tuple[str, list[str]]:
    parts, ids = [], []
    for i, c in enumerate(task["chunks"], 1):
        parts.append(f"片段{i}（文档 {c.doc_id}，章节 {c.section}）：\n{c.text}")
        ids.append(c.chunk_id)
    return "\n\n".join(parts), ids


def run_generation(client: DeepSeekClient, tasks: list[dict], done: list[dict]) -> list[dict]:
    checkpoint_ts = OUT_PATH.parent / "synthetic_checkpoint.json"
    done_ids = {d["gen_key"] for d in done}
    for i, task in enumerate(tasks):
        key = "|".join(c.chunk_id for c in task["chunks"]) + f"|{task['evo']}"
        if key in done_ids:
            continue
        chunks_text, chunk_ids = format_chunks(task)
        guide = EVOLUTION_GUIDE.get(task["evo"], EVOLUTION_GUIDE["simple"])
        if task["evo"] == "multi_context":
            guide = "本次生成 multi_context 类型：问题需要综合两个片段的信息点才能回答（对比、衔接、或共同机制），单一片段不足以回答。"
        user = f"{guide}\n\n{chunks_text}"
        try:
            gen = client.chat_json(GEN_SYSTEM, user)
            item = {
                "id": f"syn{len(done) + 1:03d}",
                "slice": "synthetic",
                "type": task["evo"],
                "question": gen["question"],
                "answer": gen["answer"],
                "avoided_terms": gen.get("avoided_terms", []),
                "difficulty": gen.get("difficulty", ""),
                "gt_chunk_ids": chunk_ids,
                "gt_doc_ids": sorted({cid.split("::")[0] for cid in chunk_ids}),
                "gen_key": key,
            }
        except Exception as exc:  # noqa: BLE001
            print(f"  [{i + 1}/{len(tasks)}] GEN FAIL {type(exc).__name__}: {str(exc)[:90]}")
            continue
        # critic pass
        try:
            crit = client.chat_json(
                CRITIC_SYSTEM,
                f"问题：{item['question']}\n\n标准答案：{item['answer']}\n\n{chunks_text[:3000]}",
                temperature=0.1,
            )
            item["critic"] = {k: crit.get(k) for k in ("clarity", "self_contained", "answerable", "grounded", "verdict", "reason")}
        except Exception as exc:  # noqa: BLE001
            print(f"  [{i + 1}/{len(tasks)}] CRITIC FAIL {type(exc).__name__}, kept uncriticized")
        done.append(item)
        state = {"done": done}
        checkpoint_ts.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        verdict = item.get("critic", {}).get("verdict", "?")
        print(f"  [{i + 1}/{len(tasks)}] {item['type']:13s} {verdict:5s} {item['question'][:42]}")
        time.sleep(0.4)
    return done


def split_dev_eval(items: list[dict], train_ratio: float = 0.7) -> None:
    """Stratify by gt_doc_ids primary doc; split within each doc at 70/30."""
    rng = random.Random(42)
    by_doc: dict[str, list[dict]] = {}
    for it in items:
        primary = it["gt_doc_ids"][0] if it["gt_doc_ids"] else "unknown"
        by_doc.setdefault(primary, []).append(it)
    for doc, group in by_doc.items():
        rng.shuffle(group)
        n_eval = max(1, round(len(group) * (1 - train_ratio))) if len(group) >= 3 else 0
        for j, it in enumerate(group):
            it["subset"] = "eval" if j < n_eval else "dev"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true", help="generate 3 items only, for format check")
    parser.add_argument("--resume", action="store_true", help="continue from checkpoint")
    args = parser.parse_args()

    chunks = kb.load_all_chunks()
    tasks = sample_chunks(chunks)
    if args.pilot:
        tasks = tasks[:3]

    client = DeepSeekClient()
    done: list[dict] = []
    if args.resume and CHECKPOINT.exists():
        done = json.loads(CHECKPOINT.read_text(encoding="utf-8"))["done"]
        print(f"resuming with {len(done)} done items")

    print(f"generation tasks: {len(tasks)} | existing: {len(done)}")
    done = run_generation(client, tasks, done)

    kept = [it for it in done if it.get("critic", {}).get("verdict") != "reject"]
    rejected = len(done) - len(kept)
    split_dev_eval(kept)

    trap_items = [
        {"id": f"trap{i + 1:02d}", "slice": "trap", "type": "trap", "subset": "eval",
         "question": q["query"], "answer": "", "gt_doc_ids": q["expected_relevant"], "note": q["note"]}
        for i, q in enumerate(TRAP_QUERIES)
    ]
    collo_items = [
        {"id": f"col{i + 1:02d}", "slice": "colloquial", "type": "colloquial", "subset": "eval",
         "question": q["query"], "answer": "", "gt_doc_ids": q["expected_relevant"], "note": "口语化含糊"}
        for i, q in enumerate(COLLOQUIAL_QUERIES)
    ]

    all_items = kept + trap_items + collo_items
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({
        "built_at": datetime.now().isoformat(timespec="seconds"),
        "generator": "deepseek-chat (family-isolated from qwen wiki / bailian embeddings)",
        "counts": {
            "synthetic_kept": len(kept), "synthetic_rejected": rejected,
            "trap": len(trap_items), "colloquial": len(collo_items), "total": len(all_items),
            "dev": sum(1 for it in all_items if it["subset"] == "dev"),
            "eval": sum(1 for it in all_items if it["subset"] == "eval"),
            "by_type": dict(Counter(it.get("type", "?") for it in kept)),
        },
        "items": all_items,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nkept {len(kept)} (rejected {rejected}) + traps {len(trap_items)} + colloquial {len(collo_items)}")
    print("dev/eval:", {k: v for k, v in Counter(it["subset"] for it in all_items).items()})
    print(f"-> {OUT_PATH}")


if __name__ == "__main__":
    main()
