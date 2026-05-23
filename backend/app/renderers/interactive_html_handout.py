from __future__ import annotations

import base64
import re
from html import escape
from pathlib import Path

import bleach

from app.schemas.render.interactive_html import InteractiveHtmlRenderModel, InteractiveHtmlRenderedUnit
from app.schemas.specs.interactive_html import InteractiveHtmlInteractionSpec, InteractiveHtmlSpec
from app.services.storage_service import LocalStorageService, StorageService


CONTROL_TAG_RE = re.compile(
    r"<(?:button|textarea|select)\b[^>]*>.*?</(?:button|textarea|select)>|<(?:input)\b[^>]*?/?>",
    re.I | re.S,
)
ARTICLE_RE = re.compile(r"<article\b(?P<attrs>[^>]*)>(?P<body>.*?)</article>", re.I | re.S)
ATTR_RE = re.compile(r'(?P<name>[A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*(?P<quote>["\'])(?P<value>.*?)(?P=quote)', re.S)
ASSET_URL_RE = re.compile(r'(?P<prefix>\s(?:src|href)=["\'])(?P<url>/api/assets/(?P<asset_id>[A-Za-z0-9_.-]+)/download)(?P<suffix>["\'])')


class InteractiveHtmlStaticHandoutRenderer:
    """Render the online interactive lesson shell as a static offline HTML handout."""

    def __init__(self, storage_service: StorageService | None = None) -> None:
        self.storage_service = storage_service or LocalStorageService()

    def render(
        self,
        content_spec: InteractiveHtmlSpec,
        render_model: InteractiveHtmlRenderModel,
        learning_events: list[dict],
        session_id: str,
    ) -> str:
        interaction_specs = {
            interaction.interaction_id: interaction
            for section in content_spec.sections
            for interaction in section.interaction_specs
        }
        events_by_section = self._events_by_section(learning_events)
        self._active_first_section_id = render_model.sections[0].section_id if render_model.sections else ""
        sections = "\n".join(
            self._section(unit, events_by_section.get(unit.section_id, []), interaction_specs)
            for unit in render_model.sections
        )
        navigation = render_model.navigation or [
            type("Navigation", (), {"section_id": unit.section_id, "title": unit.title})()
            for unit in render_model.sections
        ]
        nav_html = "\n".join(
            self._nav_item(item.section_id, item.title, index)
            for index, item in enumerate(navigation)
        )
        css = "\n\n".join(unit.css_fragment for unit in render_model.sections if unit.css_fragment.strip())
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(render_model.title)} - 离线讲义</title>
  <style>{self._shell_css()}</style>
  <style>{self._offline_css()}</style>
  <style>{css}</style>
</head>
<body>
  <div class="ih-app ih-app--offline">
    <aside class="ih-sidebar">
      <div class="ih-brand">
        <div class="ih-logo">AI</div>
        <div>
          <h1 class="ih-brand__title">{escape(render_model.title)}</h1>
          <p class="ih-brand__subtitle">离线复习讲义</p>
        </div>
      </div>
      <div class="ih-nav-title">课程目录</div>
      <nav class="ih-nav">{nav_html}</nav>
    </aside>
    <main class="ih-main">
      <section class="ih-module-card ih-module-card--hero">
        <div class="ih-hero-inner">
          <div class="ih-hero-text">
            <div class="ih-eyebrow">离线讲义 · Session {escape(session_id)}</div>
            <h2 class="ih-hero-title">{escape(render_model.title)}</h2>
            {f'<p class="ih-hero-subtitle">{escape(render_model.subtitle)}</p>' if render_model.subtitle else ''}
          </div>
        </div>
      </section>
      {sections}
      {self._citations(render_model.citations)}
    </main>
  </div>
  <script>{self._offline_script()}</script>
</body>
</html>"""

    def _section(
        self,
        unit: InteractiveHtmlRenderedUnit,
        events: list[dict],
        interaction_specs: dict[str, InteractiveHtmlInteractionSpec],
    ) -> str:
        fragment = self._staticize_fragment(unit.html_fragment)
        records = "\n".join(self._answer_record(event, interaction_specs.get(str(event.get("interaction_id") or ""))) for event in events)
        records_html = records or '<p class="ih-answer-record-empty">本节暂无已提交的学习记录。</p>'
        hidden = "" if unit.section_id == self._first_section_id else " hidden"
        return f"""<article id="{escape(unit.section_id)}" class="ih-module-card {escape(unit.style_scope_id)}" data-section-id="{escape(unit.section_id)}" data-ih-offline-section="{escape(unit.section_id)}"{hidden}>
  <div class="ih-module-card__header">
    <div class="ih-eyebrow">离线单元</div>
    <h2 class="ih-module-card__title">{escape(unit.title)}</h2>
    <p class="ih-module-card__goal">{escape(unit.learning_goal)}</p>
  </div>
  <div class="ih-fragment">{fragment}</div>
  <aside class="ih-answer-records">
    <h3>答题记录</h3>
    {records_html}
  </aside>
</article>"""

    def _staticize_fragment(self, html: str) -> str:
        html = CONTROL_TAG_RE.sub("", html)
        html = re.sub(r"\sdata-ih-action=(['\"]).*?\1", "", html, flags=re.I | re.S)
        html = re.sub(r"\sdata-ih-input-for=(['\"]).*?\1", "", html, flags=re.I | re.S)
        html = re.sub(r"\sdata-ih-feedback-for=(['\"]).*?\1", "", html, flags=re.I | re.S)
        html = self._inline_asset_urls(html)
        allowed_tags = [
            "section", "article", "div", "span", "p", "strong", "em", "b", "i", "ul", "ol", "li",
            "h1", "h2", "h3", "h4", "h5", "table", "thead", "tbody", "tr", "th", "td", "blockquote",
            "code", "pre", "img", "a", "figure", "figcaption",
        ]
        allowed_attrs = {
            "*": ["class", "id", "role", "aria-label", "aria-labelledby", "aria-describedby", "data-section-id", "data-block-id", "data-block-type"],
            "img": ["src", "alt", "width", "height"],
            "a": ["href", "title"],
        }
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, protocols=["http", "https", "data"], strip=True)

    def _inline_asset_urls(self, html: str) -> str:
        def replace(match: re.Match[str]) -> str:
            asset_id = match.group("asset_id")
            record = self.storage_service.get_record(asset_id)
            if record is None or not record.content_type.startswith("image/"):
                return match.group(0)
            encoded = base64.b64encode(self.storage_service.read_bytes(asset_id)).decode("ascii")
            return f'{match.group("prefix")}data:{record.content_type};base64,{encoded}{match.group("suffix")}'

        return ASSET_URL_RE.sub(replace, html)

    def _answer_record(self, event: dict, spec: InteractiveHtmlInteractionSpec | None) -> str:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        selected = payload.get("selected_option_ids") or []
        answer_text = payload.get("answer_text")
        student_answer = str(answer_text or self._option_text(spec, selected) or "已提交")
        correct_answer = self._option_text(spec, payload.get("correct_option_ids") or self._correct_option_ids(spec))
        status = "正确" if payload.get("is_correct") is True else "需要复习" if payload.get("is_correct") is False else "已记录"
        reference_points = payload.get("reference_points") or (spec.reference_points if spec else [])
        reference = "；".join(str(point) for point in reference_points)
        return f"""<article class="ih-answer-record">
  <p class="ih-answer-record__meta">{escape(str(event.get("event_type") or ""))} · {escape(status)}</p>
  {f'<h4>{escape(spec.prompt)}</h4>' if spec and spec.prompt else ''}
  <p><strong>学生回答：</strong>{escape(student_answer)}</p>
  {f'<p><strong>参考答案：</strong>{escape(correct_answer)}</p>' if correct_answer else ''}
  {f'<p><strong>参考要点：</strong>{escape(reference)}</p>' if reference else ''}
</article>"""

    @staticmethod
    def _events_by_section(events: list[dict]) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = {}
        for event in events:
            grouped.setdefault(str(event.get("section_id") or ""), []).append(event)
        return grouped

    @staticmethod
    def _option_text(spec: InteractiveHtmlInteractionSpec | None, option_ids: list[str]) -> str | None:
        if spec is None or not option_ids:
            return None
        selected = set(option_ids)
        labels = [option.text for option in spec.options if option.id in selected]
        return "；".join(labels) if labels else None

    @staticmethod
    def _correct_option_ids(spec: InteractiveHtmlInteractionSpec | None) -> list[str]:
        if spec is None:
            return []
        return [option.id for option in spec.options if option.is_correct is True]

    @staticmethod
    def _citations(citations: list[dict]) -> str:
        if not citations:
            return ""
        items = "".join(f"<li>{escape(str(citation.get('source_id') or citation))}</li>" for citation in citations)
        return f'<footer class="ih-citations"><h3>参考资料</h3><ul>{items}</ul></footer>'

    @property
    def _first_section_id(self) -> str:
        return getattr(self, "_active_first_section_id", "")

    def _nav_item(self, section_id: str, title: str, index: int) -> str:
        active = " active" if index == 0 else ""
        return (
            f'<button class="ih-nav__link{active}" type="button" data-ih-offline-nav="{escape(section_id)}">'
            f'<span class="ih-nav__dot"></span><span class="ih-nav__label">{escape(title)}</span></button>'
        )

    @staticmethod
    def _shell_css() -> str:
        css_path = Path(__file__).resolve().parents[3] / "frontend" / "src" / "components" / "renderers" / "InteractiveHtmlRenderer" / "styles.css"
        return css_path.read_text(encoding="utf-8")

    @staticmethod
    def _offline_css() -> str:
        return """
.ih-app--offline [data-ih-offline-section][hidden] { display: none; }
.ih-app--offline .ih-answer-records { margin-top: 28px; padding: 22px; border-radius: 22px; background: rgba(255,255,255,0.70); border: 1px solid var(--ih-line); }
.ih-app--offline .ih-answer-record { padding: 16px 18px; margin-top: 12px; border-radius: 18px; background: rgba(255,255,255,0.82); border-left: 4px solid var(--ih-primary); box-shadow: var(--ih-shadow-soft); }
.ih-app--offline .ih-answer-record__meta, .ih-app--offline .ih-answer-record-empty { color: var(--ih-muted); font-size: 13px; }
"""

    @staticmethod
    def _offline_script() -> str:
        return """
function activateOfflineSection(sectionId) {
  document.querySelectorAll('[data-ih-offline-section]').forEach(function(section) {
    var active = section.getAttribute('data-ih-offline-section') === sectionId;
    section.hidden = !active;
  });
  document.querySelectorAll('[data-ih-offline-nav]').forEach(function(button) {
    button.classList.toggle('active', button.getAttribute('data-ih-offline-nav') === sectionId);
  });
}
document.querySelectorAll('[data-ih-offline-nav]').forEach(function(button) {
  button.addEventListener('click', function() {
    activateOfflineSection(button.getAttribute('data-ih-offline-nav'));
  });
});
"""
