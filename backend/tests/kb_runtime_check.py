import json
import os
import sys
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path

from app.schemas.request import ContentGenerationRequest
from app.services.local_kb_service import LocalKBService
from app.services.rag_service import RetrievalResult
from knowledge.engine import kb_engine as kb


root = Path(sys.argv[1])
assert kb.BM25Index([]).search("knowledge") == []
texts = [(root / path).read_text(encoding="utf-8")[:2000] for path in ["README.md", "docs/architecture.md", "docs/learning-loop.md"]]
chunks = []
for index, text in enumerate(texts):
    chunks.extend(kb.chunks_from_text(str(index), str(index), text))
junk = kb.chunks_from_text("references", "References", "## References\n" + texts[0])[0]
assert kb.is_structural_junk(junk)
chunks = [c for c in chunks if not kb.is_structural_junk(c)]
kb.KB_INDEX_DIR.mkdir(parents=True)
cache = kb.KB_INDEX_DIR / "chunks.jsonl"
payload = "\n".join(json.dumps(asdict(c), ensure_ascii=False) for c in [*chunks, junk])
cache.write_text(payload, encoding="utf-8")
kb.BM25Index(chunks).save()
request = ContentGenerationRequest(content_type="interactive_html", topic="knowledge", user_prompt="knowledge retrieval")
service = LocalKBService(method="keyword")
result = service.retrieve(request, "planning")
assert isinstance(result, RetrievalResult)
assert result.status.state in {"ok", "empty"}
assert junk.chunk_id not in service._bm25.doc_ids
assert len(service._bm25.chunks) == len(chunks)
os.environ["KB_FILTER_JUNK"] = "0"
unfiltered = LocalKBService(method="keyword")
assert unfiltered.retrieve(request, "planning").status.state in {"ok", "empty"}
assert junk.chunk_id in unfiltered._bm25.doc_ids
assert kb.indexable_chunks([junk]) == [junk]
os.environ["KB_FILTER_JUNK"] = "1"
assert kb.indexable_chunks([junk]) == []
cache.write_text("invalid JSON", encoding="utf-8")
materials = ContentGenerationRequest(**{**request.model_dump(), "kb_mode":"materials_only", "attachments":[{"filename":"README.md", "content":texts[0]}]})
attachment_service = LocalKBService(method="keyword")
assert attachment_service.retrieve(materials, "planning").status.state in {"ok", "empty"}
assert attachment_service._chunks is None
assert LocalKBService(method="keyword").retrieve(request, "planning").status.state == "failed"
cache.write_text(payload, encoding="utf-8")
cloud = LocalKBService(api_key="credential-constructor-check")
cloud._ensure_loaded("platform")
assert cloud._embedder.api_key == "credential-constructor-check"
cloud._embedder.client.close()

kb.KB_RAW_DIR.mkdir(parents=True)
shutil.copyfile(root / "knowledge/examples/workbench-guide.md", kb.KB_RAW_DIR / "workbench-guide.md")
kb.load_all_chunks(force_rebuild=True)
queried = subprocess.run(
    [sys.executable, "-m", "knowledge.scripts.query", "资源重试", "--method", "keyword"],
    capture_output=True, text=True, encoding="utf-8", check=True,
)
hits = json.loads(queried.stdout)
assert hits and all(hit["title"] == "教学内容工作台使用说明" for hit in hits)
