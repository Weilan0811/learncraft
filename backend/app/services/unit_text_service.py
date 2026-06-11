from html import unescape
from html.parser import HTMLParser
import re
from typing import Any

from app.schemas.task import UnitTextChunk, UnitTextResponse


WHITESPACE_RE = re.compile(r"\s+")


class HtmlTextExtractor(HTMLParser):
    def __init__(self, target_id: str | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self.target_id = target_id
        self._capture_depth = 0 if target_id else 1
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.target_id is None:
            return
        attrs_by_name = dict(attrs)
        if self._capture_depth > 0:
            self._capture_depth += 1
            return
        if attrs_by_name.get("id") == self.target_id or attrs_by_name.get("data-block-id") == self.target_id:
            self._capture_depth = 1

    def handle_endtag(self, tag: str) -> None:
        if self.target_id is not None and self._capture_depth > 0:
            self._capture_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._capture_depth > 0:
            self._parts.append(data)

    def get_text(self) -> str:
        return normalize_text(" ".join(self._parts))


def normalize_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", unescape(text)).strip()


def extract_html_text(html_fragment: str, target_id: str | None = None) -> str:
    parser = HtmlTextExtractor(target_id=target_id)
    parser.feed(html_fragment)
    parser.close()
    return parser.get_text()


def build_unit_text_response(task_id: str, unit: dict[str, Any]) -> UnitTextResponse | None:
    render_fragment = unit.get("render_fragment")
    if not isinstance(render_fragment, dict):
        return None

    html_fragment = render_fragment.get("html_fragment")
    if not isinstance(html_fragment, str) or not html_fragment.strip():
        return None

    full_text = extract_html_text(html_fragment)
    block_manifest = render_fragment.get("block_manifest")
    chunks: list[UnitTextChunk] = []
    if isinstance(block_manifest, list):
        for block in block_manifest:
            block_id = block.get("block_id") if isinstance(block, dict) else None
            text = extract_html_text(html_fragment, block_id) if isinstance(block_id, str) else ""
            if text:
                chunks.append(UnitTextChunk(chunk_id=f"chunk-{len(chunks) + 1:02d}", text=text))

    if not chunks and full_text:
        chunks.append(UnitTextChunk(chunk_id="chunk-01", text=full_text))

    return UnitTextResponse(
        task_id=task_id,
        unit_id=str(unit["unit_id"]),
        content_type=str(unit["content_type"]),
        title=render_fragment.get("title") if isinstance(render_fragment.get("title"), str) else None,
        full_text=full_text,
        chunks=chunks,
    )
