import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.schemas.render.social_post import SocialPostExportFile, SocialPostRenderModel


class WechatClawRenderer:
    def __init__(self, skill_root: Path | None = None, storage_root: str | Path | None = None) -> None:
        settings = get_settings()
        self.skill_root = skill_root or Path(__file__).resolve().parents[1] / "skills" / "wechat-claw-skill"
        self.storage_root = Path(storage_root or settings.storage_root).resolve()

    def render(self, *, task_id: str, article_json: dict[str, Any], check: bool = True) -> SocialPostRenderModel:
        work_dir = self.storage_root / "content-generation" / task_id / "wechat"
        work_dir.mkdir(parents=True, exist_ok=True)
        article_path = work_dir / "article.json"
        html_path = work_dir / "article.html"
        article_path.write_text(json.dumps(article_json, ensure_ascii=False, indent=2), encoding="utf-8")
        cmd = [
            sys.executable,
            str(self.skill_root / "scripts" / "render_article.py"),
            str(article_path),
            "-o",
            str(html_path),
        ]
        if check:
            cmd.append("--check")
        result = subprocess.run(
            cmd,
            cwd=str(self.skill_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"wechat-claw render failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        warnings = [line for line in result.stderr.splitlines() if line.strip()]
        html = html_path.read_text(encoding="utf-8")
        meta = article_json.get("meta") or {}
        return SocialPostRenderModel(
            title=str(meta.get("title") or ""),
            digest=str(meta.get("digest") or ""),
            template=str(article_json.get("template") or ""),
            html=html,
            article_json=article_json,
            export_files=[
                SocialPostExportFile(file_type="json", path=str(article_path), label="Article JSON"),
                SocialPostExportFile(file_type="html", path=str(html_path), label="HTML"),
            ],
            warnings=warnings,
        )
