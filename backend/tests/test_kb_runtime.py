import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_real_keyword_service_in_isolated_knowledge_directory(tmp_path):
    root = Path(__file__).resolve().parents[2]
    shutil.copytree(root / "knowledge", tmp_path / "knowledge", ignore=shutil.ignore_patterns("raw", "wiki", "eval", "scripts", "__pycache__"))
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join([str(tmp_path), str(root / "backend")])
    environment["KB_EMBEDDER"] = "bailian"
    environment["KB_FILTER_JUNK"] = "1"
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("kb_runtime_check.py")), str(root)],
        cwd=tmp_path, env=environment, capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr
