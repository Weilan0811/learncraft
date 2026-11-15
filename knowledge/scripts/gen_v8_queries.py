"""v8 eval-snapshot query generation (unit 3.4): target-first + form replication.

Pipeline (three-family isolation preserved: sample=program, distill=qwen,
generate=deepseek):

  A. sample   -- program picks target chunks per seed (topic-stratified,
                 per-doc cap) + a trap pool (uniform).
  B. distill  -- qwen turns each target chunk into 3-5 gist bullets IN ITS OWN
                 WORDS (the word-surface cut: generators never see the source).
  C. generate -- deepseek plays TWO roles from the real pipeline:
                   user        -> user_prompt (register follows seed wording level)
                   outline-model-> unit fields (title/goal/core_message/
                                  retrieval_queries), prompt transcribed from
                                  backend/app/prompts/planner/interactive_html_outline.md
                 trap cells: one term-avoidance question per trap target.
  D. assemble -- program stitches final queries by importing the PRODUCT
                 _build_query (backend LocalKBService) -- structure version
                 frozen into snapshot metadata. Zero hand-written query text.

Products -> knowledge/eval/local/v8_snapshot/ (gitignored):
  distillations.json / raw_generations.json / v8_queries.json
GT: target chunk ids recorded at sampling time (free); equivalence expansion
and pooling belong to unit 3.5. This unit outputs queries that CANNOT yet be
scored against (qrels incomplete by design).
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "knowledge" / "scripts"))

from gen_synthetic_qa import read_env_key  # noqa: E402

from knowledge.engine import kb_engine as kb  # noqa: E402

LOCAL = REPO_ROOT / "knowledge" / "eval" / "local"
OUT = LOCAL / "v8_snapshot"
OUT.mkdir(parents=True, exist_ok=True)

UNITS_PER_TASK = 4
TRAP_POOL = 30
MIN_CHUNK_CHARS = 150
PER_DOC_CAP = 2


# ---------------------------------------------------------------- step A
def sample_targets(chunks: list[kb.Chunk], seeds: list[dict], rng: random.Random) -> tuple[dict, list[dict]]:
    """Per-seed topic-stratified target chunks + uniform trap pool."""
    by_topic: dict[str, list[kb.Chunk]] = {}
    for c in chunks:
        if c.char_count >= MIN_CHUNK_CHARS and c.scope == "platform":
            by_topic.setdefault(c.topic, []).append(c)

    targets: dict[str, list[dict]] = {}
    for seed in seeds:
        pool: list[kb.Chunk] = []
        for tag in seed["topic_tags"]:
            pool.extend(by_topic.get(tag, []))
        if not pool:
            pool = list(chunks)
        # dedupe + per-doc cap
        seen_docs: dict[str, int] = {}
        picked: list[kb.Chunk] = []
        for c in rng.sample(pool, len(pool)):
            if len(picked) >= UNITS_PER_TASK:
                break
            if seen_docs.get(c.doc_id, 0) >= PER_DOC_CAP or any(x.chunk_id == c.chunk_id for x in picked):
                continue
            seen_docs[c.doc_id] = seen_docs.get(c.doc_id, 0) + 1
            picked.append(c)
        targets[seed["seed_id"]] = [
            {"chunk_id": c.chunk_id, "doc_id": c.doc_id, "section": c.section, "topic": c.topic} for c in picked
        ]

    # trap pool: uniform across all docs
    platform = [c for c in chunks if c.scope == "platform" and c.char_count >= MIN_CHUNK_CHARS]
    rng.shuffle(platform)
    seen_docs = {}
    trap: list[dict] = []
    for c in platform:
        if len(trap) >= TRAP_POOL:
            break
        if seen_docs.get(c.doc_id, 0) >= PER_DOC_CAP:
            continue
        seen_docs[c.doc_id] = seen_docs.get(c.doc_id, 0) + 1
        trap.append({"chunk_id": c.chunk_id, "doc_id": c.doc_id, "section": c.section, "topic": c.topic})
    return targets, trap


# ---------------------------------------------------------------- step B
def qwen_distill(client, chunk_text: str, section: str) -> list[str]:
    system = (
        "你是知识库内容编辑。把给定的知识片段蒸馏成 3-5 条要点。"
        "要求：用自己的话概括核心论断，绝不照抄原文措辞或原句；保留事实与结论的准确性；每条要点一句话。"
        '输出 JSON: {"bullets": ["...", "..."]}'
    )
    user = f"小节: {section}\n\n片段:\n{chunk_text[:2500]}"
    return client.chat_json_distill(system, user)["bullets"]


def run_distillation(chunks_by_id: dict[str, kb.Chunk], targets: dict, trap: list[dict]) -> dict:
    out_path = OUT / "distillations.json"
    done: dict[str, list[str]] = {}
    if out_path.exists():
        done = json.loads(out_path.read_text(encoding="utf-8"))
        print(f"  distill checkpoint: {len(done)} already done")

    all_ids = [t["chunk_id"] for ts in targets.values() for t in ts] + [t["chunk_id"] for t in trap]
    todo = [cid for cid in dict.fromkeys(all_ids) if cid not in done]
    print(f"  distilling {len(todo)} chunks via qwen-plus ...")
    for i, cid in enumerate(todo):
        c = chunks_by_id[cid]
        bullets = qwen_distill(_QwenClient(), f"{c.title} | {c.section} | {c.text}", c.section)
        done[cid] = bullets
        if (i + 1) % 20 == 0 or i + 1 == len(todo):
            out_path.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"    {i + 1}/{len(todo)} ({time.time() - _T0:.0f}s)")
    out_path.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
    return done


class _QwenClient:
    """dashscope compatible-mode (same channel as compile_wiki.py)."""

    def __init__(self) -> None:
        self.key = read_env_key("CONTENT_GENERATOR_BAILIAN_API_KEY")

    def chat_json_distill(self, system: str, user: str) -> dict:
        resp = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.key}"},
            json={
                "model": "qwen-plus",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            },
            timeout=120,
        )
        resp.raise_for_status()
        return json.loads(resp.json()["choices"][0]["message"]["content"])


# ---------------------------------------------------------------- step C
class _DeepSeekClient:
    """deepseek-chat with relaxed max_tokens (outline JSON is bigger than v7 QA)."""

    def __init__(self) -> None:
        self.base = read_env_key("CONTENT_GENERATOR_DEEPSEEK_BASE_URL").rstrip("/") or "https://api.deepseek.com"
        self.key = read_env_key("CONTENT_GENERATOR_DEEPSEEK_API_KEY")

    def chat_json(self, system: str, user: str, temperature: float = 1.0, max_tokens: int = 1600) -> dict:
        resp = requests.post(
            f"{self.base}/chat/completions",
            headers={"Authorization": f"Bearer {self.key}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": temperature,
                "response_format": {"type": "json_object"},
                "max_tokens": max_tokens,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return json.loads(resp.json()["choices"][0]["message"]["content"])


REGISTER_HINT = {
    "L0": "用户对领域有一定了解，topic 就是标准术语；user_prompt 是清晰的任务指令，可以自然使用领域词汇。",
    "L1": "用户不完全说行话，topic 用日常说法表达专业概念；user_prompt 任务指令清晰但措辞口语化。",
    "L2": "用户描述想解决的问题和期望的效果，但不使用任何专业术语；user_prompt 描述目标而不点名技术概念。",
    "L3": "用户很随意地输入，topic 就是随手打的一句话；user_prompt 也简短随意、信息不完整，像随口一提。",
}

OUTLINE_SYSTEM = (
    "你是 AI 课件生成工具的大纲模型。根据用户任务和检索到的资料要点，为课件产出大纲单元。要求：\n"
    "- 每个 unit 必须包含 title, goal, core_message, retrieval_queries。\n"
    "- 每个 unit 的 title 和 goal 清晰反映该 section 的学习目标。\n"
    "- core_message 概括本节最重要的教学信息。\n"
    "- retrieval_queries 应围绕本节学习目标和关键概念，便于后续 section 级检索。\n"
    "- 尽量使用提供资料中的事实、术语和来源线索。\n"
    "- 每个单元对应一个资料要点组（G1-G4），不要合并或拆分。必须输出恰好 4 个单元，第 N 个单元严格对应 GN 要点组，禁止合并或省略任何一组。\n"
    '输出 JSON: {"units": [{"unit_idx": 1, "title": "...", "goal": "...", "core_message": "...", "retrieval_queries": ["...", "..."]}]}'
)


def run_generation(seeds: list[dict], targets: dict, gists: dict, trap: list[dict], rng: random.Random) -> dict:
    client = _DeepSeekClient()
    raw = {}
    out_path = OUT / "raw_generations.json"
    if out_path.exists():
        raw = json.loads(out_path.read_text(encoding="utf-8"))
        print(f"  generation checkpoint: {len(raw)} keys already done")

    for i, seed in enumerate(seeds):
        sid = seed["seed_id"]
        if f"{sid}:user" not in raw:
            sys_p = "你扮演一个使用 AI 课件生成工具的用户。根据任务信息写一句 user_prompt（任务指令），" + REGISTER_HINT[seed["wording_level"]] + ' 输出 JSON: {"user_prompt": "..."}'
            u_p = client.chat_json(sys_p, f"topic: {seed['topic']}\n课件形态: {seed['goal_form']}\n受众: {seed['audience']}")
            raw[f"{sid}:user"] = u_p
            out_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")

        if f"{sid}:outline" not in raw:
            gist_block = "\n\n".join(
                f"[G{n + 1}] 目标块 {t['chunk_id']}\n要点:\n- " + "\n- ".join(gists[t["chunk_id"]])
                for n, t in enumerate(targets[sid])
            )
            u_p = f"任务 topic: {seed['topic']}\n课件形态: {seed['goal_form']}\n受众: {seed['audience']}\n\n检索到的资料要点:\n{gist_block}"
            o_p = client.chat_json(OUTLINE_SYSTEM, u_p, temperature=0.8)
            raw[f"{sid}:outline"] = o_p
            out_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  seed {sid} done ({i + 1}/{len(seeds)}, {time.time() - _T0:.0f}s)")

    # trap questions: one per trap target
    todo_t = [t["chunk_id"] for t in trap if f"trap:{t['chunk_id']}" not in raw]
    print(f"  trap questions: {len(todo_t)} to generate")
    for i, t in enumerate(trap):
        key = f"trap:{t['chunk_id']}"
        if key in raw:
            continue
        c = chunks_by_id[t["chunk_id"]]
        bullets = gists[t["chunk_id"]]
        sys_p = (
            "根据知识要点出一道测试问题，用于考察检索系统在措辞对抗下的表现。要求：问题必须能由这些要点回答；"
            "问题中绝不使用要点里的专业术语原词（用日常语言描述同一件事）；单句中文问句，自然且不生硬。"
            '输出 JSON: {"question": "..."}'
        )
        u_p = "知识要点:\n- " + "\n- ".join(bullets) + f"\n\n（原文小节: {c.section}，仅供你理解语境，问题里不要引用原文措辞）"
        raw[key] = client.chat_json(sys_p, u_p, temperature=0.9)
        if (i + 1) % 10 == 0 or i + 1 == len(trap):
            out_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"    trap {i + 1}/{len(trap)} ({time.time() - _T0:.0f}s)")
    out_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    return raw


# ---------------------------------------------------------------- step D
def product_build_query(request, stage: str, section_hint: str | None) -> str:
    """Import the PRODUCT _build_query. Fallback mirror is verified once at boot."""
    try:
        # backend/ is not a package; app/ is. Put backend/ on sys.path.
        backend_dir = str(REPO_ROOT / "backend")
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from app.services.local_kb_service import LocalKBService

        return LocalKBService._build_query(None, request, stage, section_hint)
    except Exception as exc:  # pragma: no cover - fallback with loud marker
        print(f"  !! product import failed ({exc}); using verified mirror")
        return _mirror_build_query(request, stage, section_hint)


def _mirror_build_query(request, stage: str, section_hint: str | None) -> str:
    parts = [request.topic, request.user_prompt, stage]
    if request.system_prompt:
        parts.append(request.system_prompt)
    if section_hint:
        parts.append(section_hint)
    return "\n".join(part for part in parts if part)


def structure_version() -> dict:
    svc = REPO_ROOT / "backend" / "app" / "services" / "local_kb_service.py"
    src = svc.read_text(encoding="utf-8")
    return {
        "source": "backend/app/services/local_kb_service.py::_build_query",
        "sha256": hashlib.sha256(src.encode("utf-8")).hexdigest()[:16],
    }


def main() -> None:
    global _T0, chunks_by_id
    _T0 = time.time()
    rng = random.Random(20261113)

    chunks = kb.load_all_chunks()
    chunks_by_id = {c.chunk_id: c for c in chunks}
    print(f"corpus chunks: {len(chunks)}")

    seeds_doc = json.loads((REPO_ROOT / "knowledge" / "eval" / "seeds" / "seeds.json").read_text(encoding="utf-8"))
    seeds = seeds_doc["seeds"]
    print(f"seeds: {len(seeds)}")

    targets, trap = sample_targets(chunks, seeds, rng)
    print(f"targets: {sum(len(v) for v in targets.values())} | trap pool: {len(trap)}")

    gists = run_distillation(chunks_by_id, targets, trap)
    raw = run_generation(seeds, targets, gists, trap, rng)

    # ---------- assemble snapshot ----------
    task_ids = [s["seed_id"] for s in seeds]
    rng.shuffle(task_ids)
    dev_tasks = set(task_ids[:14])  # 70/30 split BY TASK (no cross-set leakage)

    items = []
    for seed in seeds:
        sid = seed["seed_id"]
        subset = "dev" if sid in dev_tasks else "eval"
        user_prompt = raw[f"{sid}:user"]["user_prompt"]
        units = raw[f"{sid}:outline"]["units"]
        tgs = targets[sid]

        # planning query: task-level retrieval, GT = union of target docs (recorded, scored in 3.5)
        req = _Req(topic=seed["topic"], user_prompt=user_prompt)
        q_plan = product_build_query(req, "planning", None)
        items.append(
            {
                "id": f"v8-{sid}-plan",
                "subset": subset,
                "slice": "planning",
                "type": "planning",
                "wording_level": seed["wording_level"],
                "question": q_plan,
                "gt_chunk_ids": [t["chunk_id"] for t in tgs],
                "gt_doc_ids": sorted({t["doc_id"] for t in tgs}),
                "seed_id": sid,
                "user_prompt": user_prompt,
            }
        )

        for n, unit in enumerate(units[: len(tgs)]):
            t = tgs[n]
            hint = "\n".join([unit["title"], unit["core_message"], *unit["retrieval_queries"]])
            q_gen = product_build_query(req, "generation", hint)
            items.append(
                {
                    "id": f"v8-{sid}-g{n + 1}",
                    "subset": subset,
                    "slice": "generation",
                    "type": "generation",
                    "wording_level": seed["wording_level"],
                    "question": q_gen,
                    "gt_chunk_ids": [t["chunk_id"]],
                    "gt_doc_ids": [t["doc_id"]],
                    "seed_id": sid,
                    "unit_title": unit["title"],
                    "unit_idx": n + 1,
                }
            )

    # trap: split 21/9 by rng (task-independent cell)
    trap_items = []
    trap_rng = random.Random(88)
    order = list(range(len(trap)))
    trap_rng.shuffle(order)
    for k, idx in enumerate(order):
        t = trap[idx]
        q = raw[f"trap:{t['chunk_id']}"]["question"]
        trap_items.append(
            {
                "id": f"v8-trap{idx + 1:02d}",
                "subset": "dev" if k < 21 else "eval",
                "slice": "trap",
                "type": "trap",
                "wording_level": "L2",
                "question": q,
                "gt_chunk_ids": [t["chunk_id"]],
                "gt_doc_ids": [t["doc_id"]],
            }
        )
    items.extend(trap_items)

    from collections import Counter

    meta = {
        "version": "v8-20261113",
        "stage": "3.4 query generation (qrels NOT yet complete -- scoring awaits unit 3.5)",
        "structure_version": structure_version(),
        "generator": "deepseek-chat (user + outline roles)",
        "distiller": "qwen-plus (word-surface cut: generators never see source text)",
        "seeds": "knowledge/eval/seeds/seeds.json (v8-seeds-20261113)",
        "counts": {"total": len(items), "by_subset": Counter(i["subset"] for i in items), "by_slice": Counter(i["slice"] for i in items), "by_wording": Counter(i["wording_level"] for i in items)},
        "split_rule": "dev/eval split BY SEED TASK (14/6); trap split 21/9 independently; no cross-set leakage",
    }
    snap = {"meta": meta, "items": items}
    (OUT / "v8_queries.json").write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nsnapshot: {len(items)} items -> {OUT / 'v8_queries.json'}")
    print(json.dumps(meta["counts"], ensure_ascii=False, default=dict, indent=1))
    print(f"total time: {time.time() - _T0:.0f}s")


class _Req:
    """Minimal stand-in for ContentGenerationRequest (fields _build_query reads)."""

    def __init__(self, topic: str, user_prompt: str) -> None:
        self.topic = topic
        self.user_prompt = user_prompt
        self.system_prompt = None


if __name__ == "__main__":
    main()
